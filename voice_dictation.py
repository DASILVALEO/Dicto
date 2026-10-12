#!/usr/bin/env python3
"""
voice_dictation.py
==================
Dictado por voz global con Whisper en la nube (Groq u OpenAI).

Uso:
    python voice_dictation.py
    python voice_dictation.py --test-mic
    python voice_dictation.py --set-key <GROQ_API_KEY>

Hotkey por defecto: Ctrl+Shift+Space (toggle grabar/parar)
Hotkey para salir:  Ctrl+Alt+Q
Idioma:              espanol (cambiar "language" en ~/.dictation_config.json)

Dependencias:
    pip install keyboard sounddevice requests pyperclip numpy
"""
import os
import sys
import io
import json
import time
import wave
import threading
import tempfile
import argparse
import struct
from pathlib import Path
from typing import Optional

# Dependencias externas (instaladas por requirements.txt)
import keyboard
import sounddevice as sd
import requests
import pyperclip

# Overlay visual
try:
    from overlay import DictationOverlay
    _OVERLAY_OK = True
except Exception as e:
    _OVERLAY_OK = False
    print(f"[WARN] Overlay no disponible: {e}")
    DictationOverlay = None

# ============================ Configuracion ============================
CONFIG_PATH = Path.home() / ".dictation_config.json"

DEFAULT_CONFIG = {
    "provider": "minimax",             # "minimax", "groq" or "openai"
    "minimax_api_key": "",
    "groq_api_key": "",
    "openai_api_key": "",
    "language": "es",                  # "es", "en", or "" para auto
    "hotkey": "ctrl+shift+space",      # toggle: pulsa para grabar, otra vez para parar
    "quit_hotkey": "ctrl+alt+q",
    "sample_rate": 16000,              # Whisper/ASR espera 16 kHz
    "channels": 1,
    "min_duration_seconds": 0.1,
    "input_device": None,              # None = default del sistema
    "auto_paste": True,                # Si False, solo copia al portapapeles
    "show_notifications": False,
    "log_to_file": True,
}

PROVIDERS = {
    "minimax": {
        "url": "https://api.minimax.io/v1/speech_to_text",
        "model": "asr-1.0",
        "key_field": "minimax_api_key",
        "free_tier": False,
        "label": "MiniMax (ASR-1.0, 20+ idiomas, incluye espanol)",
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/audio/transcriptions",
        "model": "whisper-large-v3",
        "key_field": "groq_api_key",
        "free_tier": True,
        "label": "Groq (FREE tier, super rapido, recomendado)",
    },
    "openai": {
        "url": "https://api.openai.com/v1/audio/transcriptions",
        "model": "whisper-1",
        "key_field": "openai_api_key",
        "free_tier": False,
        "label": "OpenAI (Pago, ~$0.006/min)",
    },
}

# ============================ Estado ============================
_is_recording = False
_audio_chunks: list[bytes] = []
_stream: Optional[sd.InputStream] = None
_state_lock = threading.Lock()
_stop_requested = False
_quit_event = threading.Event()
_overlay: Optional["DictationOverlay"] = None
_current_level: float = 0.0


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            # utf-8-sig strips BOM if present
            cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig")))
        except Exception as e:
            print(f"[WARN] No se pudo leer {CONFIG_PATH}: {e}")
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def get_config() -> dict:
    return load_config()


# ============================ Audio ============================
def _audio_callback(indata, frames, time_info, status):
    """Callback de sounddevice: captura cuadros de audio y mide nivel (peak)."""
    if _is_recording and not _stop_requested:
        data = bytes(indata)
        _audio_chunks.append(data)
        # Peak detection agresivo para VU meter responsivo (como test de micro de Windows)
        global _current_level
        try:
            n = len(data) // 2
            if n > 0:
                samples = struct.unpack(f"<{n}h", data)
                peak = max(abs(s) for s in samples) / 32768.0
                if peak > _current_level:
                    _current_level = peak
                else:
                    _current_level = max(_current_level * 0.80, peak)
        except Exception:
            pass


def _start_stream(cfg: dict) -> None:
    global _stream
    kwargs = dict(
        samplerate=cfg["sample_rate"],
        channels=cfg["channels"],
        dtype="int16",
        callback=_audio_callback,
    )
    if cfg.get("input_device") is not None:
        kwargs["device"] = cfg["input_device"]
    _stream = sd.InputStream(**kwargs)
    _stream.start()


def _stop_stream() -> None:
    global _stream
    if _stream is not None:
        try:
            _stream.stop()
            _stream.close()
        except Exception:
            pass
        _stream = None


def _save_wav(audio_bytes: bytes, cfg: dict) -> Path:
    wav_path = Path(tempfile.mktemp(suffix=".wav"))
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(cfg["channels"])
        wf.setsampwidth(2)
        wf.setframerate(cfg["sample_rate"])
        wf.writeframes(audio_bytes)
    return wav_path


# ============================ API ============================
import math
def transcribe(wav_path: Path, cfg: dict) -> str:
    provider_name = cfg["provider"]
    if provider_name not in PROVIDERS:
        raise RuntimeError(f"Proveedor desconocido: {provider_name}")
    provider = PROVIDERS[provider_name]
    api_key = cfg.get(provider["key_field"], "").strip()
    if not api_key:
        raise RuntimeError(
            f"API key no configurada ({provider['key_field']}). "
            f"Edita {CONFIG_PATH} o usa: python voice_dictation.py --set-key TU_API_KEY"
        )
    headers = {"Authorization": f"Bearer {api_key}"}

    if provider_name == "minimax":
        return _transcribe_minimax(wav_path, api_key, cfg)
    return _transcribe_openai_compatible(wav_path, headers, provider, cfg)


def _transcribe_openai_compatible(wav_path: Path, headers: dict, provider: dict, cfg: dict) -> str:
    data = {
        "model": provider["model"],
        "response_format": "json",
    }
    if cfg.get("language"):
        data["language"] = cfg["language"]
    with open(wav_path, "rb") as f:
        files = {"file": (wav_path.name, f, "audio/wav")}
        r = requests.post(provider["url"], headers=headers, files=files,
                          data=data, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"API {r.status_code}: {r.text[:300]}")
    return r.json().get("text", "").strip()


def _transcribe_minimax(wav_path: Path, api_key: str, cfg: dict) -> str:
    """MiniMax STT: multipart/form-data, model=asr-1.0, language header BCP-47."""
    url = "https://api.minimax.io/v1/speech_to_text"
    headers = {"Authorization": f"Bearer {api_key}"}
    lang = cfg.get("language") or ""
    if lang:
        headers["language"] = lang
    with open(wav_path, "rb") as f:
        files = {"file": (wav_path.name, f, "audio/wav")}
        data = {"model": "asr-1.0", "response_format": "json"}
        r = requests.post(url, headers=headers, files=files, data=data, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"MiniMax STT {r.status_code}: {r.text[:300]}")
    return r.json().get("text", "").strip()


# ============================ Flujo principal ============================
def start_recording(cfg: dict) -> None:
    global _is_recording
    with _state_lock:
        if _is_recording:
            return
        _audio_chunks.clear()
        try:
            _start_stream(cfg)
        except Exception as e:
            print(f"\n[ERROR] No se pudo abrir el microfono: {e}")
            if _overlay:
                _overlay.set_state("error", f"Mic: {e}")
            return
        _is_recording = True
    print("\n[REC]  Mic grabando. Pulsa de nuevo la hotkey para parar.",
          flush=True)
    if _overlay:
        _overlay.set_state("recording", "Grabando...")


def stop_and_process(cfg: dict) -> None:
    global _is_recording
    with _state_lock:
        if not _is_recording:
            return
        _is_recording = False
    _stop_stream()
    global _current_level
    _current_level = 0.0
    if _overlay:
        _overlay.set_level(0.0)
    if not _audio_chunks:
        print("\n[REC]  Sin audio capturado.", flush=True)
        if _overlay:
            _overlay.set_state("done", "Sin audio")
        return
    audio_bytes = b"".join(_audio_chunks)
    _audio_chunks.clear()
    min_bytes = int(cfg["sample_rate"] * 2 * cfg["min_duration_seconds"])
    if len(audio_bytes) < min_bytes:
        duration = len(audio_bytes) / (cfg["sample_rate"] * 2)
        print(f"\n[REC]  Audio muy corto ({duration:.2f}s), ignorado.", flush=True)
        if _overlay:
            _overlay.set_state("done", f"Muy corto ({duration:.1f}s)")
        return
    if _overlay:
        _overlay.set_state("processing", "Transcribiendo...")
    wav_path = None
    try:
        wav_path = _save_wav(audio_bytes, cfg)
        duration = len(audio_bytes) / (cfg["sample_rate"] * 2)
        print(f"[API]  Enviando {duration:.1f}s a {cfg['provider']} ...",
              end="", flush=True)
        text = transcribe(wav_path, cfg)
    except Exception as e:
        print(f"\n[ERROR] Transcripcion fallo: {e}", flush=True)
        if _overlay:
            _overlay.set_state("error", f"Error: {str(e)[:40]}")
        return
    finally:
        if wav_path is not None:
            try:
                wav_path.unlink()
            except OSError:
                pass
    if not text:
        print("\n[OUT]  (texto vacio)", flush=True)
        if _overlay:
            _overlay.set_state("done", "Vacio")
        return
    print(f"\n[OUT]  {text}", flush=True)
    if _overlay:
        _overlay.set_state("done", f"OK: {text[:40]}")
    if cfg.get("auto_paste", True):
        try:
            pyperclip.copy(text)
            time.sleep(0.05)
            keyboard.press_and_release("ctrl+v")
        except Exception as e:
            print(f"[WARN] No se pudo pegar automaticamente: {e}")


def toggle(cfg: dict) -> None:
    if _is_recording:
        stop_and_process(cfg)
    else:
        start_recording(cfg)


# ============================ Overlay thread ============================
def _overlay_level_thread():
    """Envia el nivel de audio al overlay periodicamente."""
    while not _quit_event.is_set():
        if _is_recording and _overlay:
            _overlay.set_level(_current_level)
        _quit_event.wait(0.05)


# ============================ Utilidades ============================
def test_microphone(cfg: dict) -> None:
    print("Probando microfono por 3 segundos...")
    try:
        rec = sd.rec(int(3 * cfg["sample_rate"]), samplerate=cfg["sample_rate"],
                     channels=cfg["channels"], dtype="int16")
        sd.wait()
        peak = float(rec.max())
        rms = float((rec.astype("float32") ** 2).mean() ** 0.5)
        wav_path = _save_wav(rec.tobytes(), cfg)
        size = wav_path.stat().st_size
        wav_path.unlink()
        print(f"OK. Pico={peak:.0f}  RMS={rms:.1f}  WAV={size} bytes")
        if peak < 100:
            print("[WARN] Senal muy baja. Habla mas fuerte o sube el volumen del micro.")
    except Exception as e:
        print(f"FALLO: {e}")


def list_devices() -> None:
    print("Dispositivos de audio disponibles:")
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0:
            print(f"  [{i}] {d['name']}  (entradas={d['max_input_channels']})")


def cmd_set_key(cfg: dict, provider: str, key: str) -> None:
    if provider not in PROVIDERS:
        print(f"Proveedores validos: {', '.join(PROVIDERS)}")
        return
    field = PROVIDERS[provider]["key_field"]
    cfg[field] = key
    save_config(cfg)
    print(f"OK. Guardado en {CONFIG_PATH}")
    print("Ahora puedes iniciar la app con: python voice_dictation.py")


def cmd_set(cfg: dict, key: str, value) -> None:
    cfg[key] = value
    save_config(cfg)
    print(f"OK. {key} = {value}")


# ============================ Main ============================
def print_banner(cfg: dict) -> None:
    print("=" * 60)
    print("   Voice Dictation (Whisper en la nube)")
    print("=" * 60)
    provider = PROVIDERS.get(cfg["provider"], {})
    has_key = bool(cfg.get(provider.get("key_field", ""), "")) if provider else False
    print(f"   Provider : {cfg['provider']} ({provider.get('label', '')})")
    print(f"   API key  : {'OK' if has_key else 'NO CONFIGURADA'}")
    print(f"   Idioma   : {cfg['language'] or 'auto-detect'}")
    print(f"   Hotkey   : {cfg['hotkey']}  (toggle)")
    print(f"   Salir    : {cfg['quit_hotkey']}")
    print(f"   Config   : {CONFIG_PATH}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Dictado por voz con Whisper (nube)")
    parser.add_argument("--test-mic", action="store_true", help="Probar microfono")
    parser.add_argument("--list-devices", action="store_true", help="Listar microfonos")
    parser.add_argument("--set-key", metavar="APIKEY", help="Guardar Groq API key")
    parser.add_argument("--provider", choices=list(PROVIDERS),
                        help="Cambiar proveedor")
    parser.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"),
                        help="Cambiar parametro de config (ej: --set language en)")
    parser.add_argument("--show-config", action="store_true")
    args = parser.parse_args()

    cfg = get_config()

    if args.show_config:
        print(json.dumps(cfg, indent=2, ensure_ascii=False))
        return
    if args.list_devices:
        list_devices()
        return
    if args.test_mic:
        test_microphone(cfg)
        return
    if args.provider:
        cfg["provider"] = args.provider
        save_config(cfg)
        print(f"Proveedor cambiado a: {args.provider}")
    if args.set_key:
        cmd_set_key(cfg, args.provider or cfg["provider"], args.set_key)
        return
    if args.set:
        cmd_set(cfg, args.set[0], args.set[1])
        return

    print_banner(cfg)
    provider = PROVIDERS.get(cfg["provider"], {})
    if not cfg.get(provider.get("key_field", ""), ""):
        print()
        print(f"  >> Falta API key. Para configurar:")
        print(f"     python voice_dictation.py --set-key gsk_xxxxxxxxxxxxxxxx")
        print(f"     (Crea una gratis en https://console.groq.com/keys)")
        print()

    print(f"  >> Pulsa la hotkey [{cfg['hotkey']}] para empezar/detener")
    print(f"  >> Pulsa [{cfg['quit_hotkey']}] para salir")
    print()

    # Registrar atajos globales (se re-registran periodicamente para sobrevivir a suspender/hibernar)
    def _register_hotkeys():
        try:
            keyboard.unhook_all()
            # Tecla de dictado: si es una combinacion (contiene +) usa add_hotkey,
            # si es una sola tecla (ej 'alt gr') usa on_press_key que es mas confiable
            hk = cfg["hotkey"]
            if "+" in hk:
                keyboard.add_hotkey(hk, lambda: toggle(cfg), suppress=False)
            else:
                # Callback ignora el evento; el toggle usa el estado interno
                keyboard.on_press_key(hk, lambda e: toggle(cfg), suppress=False)
            # Quit hotkey
            qh = cfg["quit_hotkey"]
            if "+" in qh:
                keyboard.add_hotkey(qh, lambda: (print("\n[EXIT] Cerrando...", flush=True), _quit_event.set()))
            else:
                keyboard.on_press_key(qh, lambda e: (print("\n[EXIT] Cerrando...", flush=True), _quit_event.set()))
            return True
        except Exception as e:
            print(f"[WARN] Registro de hotkey fallo: {e}")
            return False

    def _heartbeat():
        # Re-registra hotkeys cada 30s. La libreria keyboard pierde hooks despues de suspender.
        while not _quit_event.is_set():
            _quit_event.wait(30)
            if _quit_event.is_set():
                break
            _register_hotkeys()

    _register_hotkeys()
    threading.Thread(target=_heartbeat, daemon=True).start()

    # Iniciar overlay visual (Tkinter)
    global _overlay
    if _OVERLAY_OK and DictationOverlay is not None:
        try:
            _overlay = DictationOverlay()
            _overlay.start()
            _overlay.set_state("ready", "Listo")
            print("[OK] Overlay visual iniciado (ventana arriba-centro)")
        except Exception as e:
            print(f"[WARN] Overlay no se pudo iniciar: {e}")
            _overlay = None
    else:
        print("[INFO] Overlay no disponible (Tkinter fallo)")

    # Hilo que actualiza nivel de audio en el overlay
    threading.Thread(target=_overlay_level_thread, daemon=True).start()

    try:
        _quit_event.wait()  # Espera hasta que quit se active
    except KeyboardInterrupt:
        print("\n[EXIT] Ctrl+C - Cerrando")


if __name__ == "__main__":
    main()
