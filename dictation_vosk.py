#!/usr/bin/env python3
"""
dictation_vosk.py
=================
Dictado por voz OFFLINE con Vosk (español).

- Modelo local:  %LOCALAPPDATA%\\vosk-models\\vosk-model-small-es-0.42
- Hotkey:        Ctrl+Shift+Space  (toggle grabar/parar)
- Salir:         Ctrl+Alt+Q
- Pega el texto donde esté el cursor via Ctrl+V (clipboard)

Uso:
    python dictation_vosk.py
    python dictation_vosk.py --test-mic
    python dictation_vosk.py --set-model PATH
    python dictation_vosk.py --set-hotkey ctrl+shift+x
"""
import os
import sys
import json
import time
import queue
import argparse
import threading
from pathlib import Path

import keyboard
import sounddevice as sd
import pyperclip
from vosk import Model, KaldiRecognizer, SetLogLevel

# ============================ Configuracion ============================
CONFIG_PATH = Path.home() / ".dictation_vosk.json"
DEFAULT_MODEL_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "vosk-models" / "vosk-model-small-es-0.42"

DEFAULT_CONFIG = {
    "model_path": str(DEFAULT_MODEL_DIR),
    "hotkey": "ctrl+shift+space",
    "quit_hotkey": "ctrl+alt+q",
    "sample_rate": 16000,
    "channels": 1,
    "input_device": None,
    "auto_paste": True,
    "max_duration_seconds": 60,
}


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


# ============================ Estado ============================
_is_recording = False
_audio_q: "queue.Queue[bytes]" = queue.Queue()
_stream: "sd.InputStream | None" = None
_state_lock = threading.Lock()
_final_text: list[str] = []
_partial_text: str = ""


def audio_callback(indata, frames, time_info, status):
    if status:
        pass  # silenciar warnings
    if _is_recording:
        _audio_q.put(bytes(indata))


def find_model() -> str:
    candidates = [
        Path.home() / "vosk-models" / "vosk-model-small-es-0.42",
        Path(os.environ.get("LOCALAPPDATA", "")) / "vosk-models" / "vosk-model-small-es-0.42",
        Path(os.environ.get("LOCALAPPDATA", "")) / "vosk-models" / "vosk-model-es-0.42",
        Path(os.environ.get("USERPROFILE", "")) / "vosk-models" / "vosk-model-small-es-0.42",
    ]
    for c in candidates:
        if c.is_dir() and (c / "am").exists():
            return str(c)
    return ""


# ============================ Loop principal ============================
def start_recording(cfg: dict) -> None:
    global _stream, _final_text
    with _state_lock:
        if _is_recording:
            return
        _final_text = []
        # Vaciar cola
        while not _audio_q.empty():
            try:
                _audio_q.get_nowait()
            except queue.Empty:
                break
        kwargs = dict(
            samplerate=cfg["sample_rate"],
            channels=cfg["channels"],
            dtype="int16",
            callback=audio_callback,
        )
        if cfg.get("input_device") is not None:
            kwargs["device"] = cfg["input_device"]
        try:
            _stream = sd.InputStream(**kwargs)
            _stream.start()
        except Exception as e:
            print(f"\n[ERROR] Micrófono: {e}", flush=True)
            return
    globals()["_is_recording"] = True
    print("\n[REC]  🎤 Grabando... (pulsa de nuevo la hotkey para parar)",
          flush=True)


def stop_and_paste(cfg: dict, model: Model) -> None:
    global _is_recording, _stream
    with _state_lock:
        if not _is_recording:
            return
        _is_recording = False
    if _stream is not None:
        try:
            _stream.stop()
            _stream.close()
        except Exception:
            pass
        _stream = None

    # Procesar todo el audio encolado
    rec = KaldiRecognizer(model, cfg["sample_rate"])
    rec.SetWords(True)
    full_text_parts: list[str] = []
    chunks = 0
    while not _audio_q.empty():
        try:
            data = _audio_q.get_nowait()
        except queue.Empty:
            break
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            txt = res.get("text", "").strip()
            if txt:
                full_text_parts.append(txt)
        chunks += 1
    res = json.loads(rec.FinalResult())
    txt = res.get("text", "").strip()
    if txt:
        full_text_parts.append(txt)

    # Vaciar
    while not _audio_q.empty():
        try:
            _audio_q.get_nowait()
        except queue.Empty:
            break

    text = " ".join(full_text_parts).strip()
    if not text:
        print("\n[OUT]  (sin texto reconocido)", flush=True)
        return

    print(f"\n[OUT]  {text}", flush=True)

    if cfg.get("auto_paste", True):
        try:
            pyperclip.copy(text)
            time.sleep(0.05)
            keyboard.press_and_release("ctrl+v")
        except Exception as e:
            print(f"[WARN] No se pudo pegar: {e}", flush=True)


def toggle(cfg: dict, model: Model) -> None:
    if _is_recording:
        stop_and_paste(cfg, model)
    else:
        start_recording(cfg)


# ============================ Utilidades ============================
def list_devices() -> None:
    print("Dispositivos de entrada:")
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0:
            print(f"  [{i}] {d['name']}  (entradas={d['max_input_channels']})")


def test_mic(cfg: dict) -> None:
    print("Probando micrófono 3 segundos (Vosk pasa audio real)...")
    rec_data: list[bytes] = []

    def cb(indata, frames, time_info, status):
        rec_data.append(bytes(indata))

    s = sd.InputStream(samplerate=cfg["sample_rate"], channels=cfg["channels"],
                       dtype="int16", callback=cb)
    s.start()
    time.sleep(3)
    s.stop()
    s.close()
    audio = b"".join(rec_data)
    print(f"Capturado {len(audio)} bytes ({len(audio)/(cfg['sample_rate']*2):.2f}s)")
    if len(audio) < 1000:
        print("[WARN] No se capturó audio. Verifica el micrófono.")
        return
    model_path = find_model() or cfg["model_path"]
    if not Path(model_path).is_dir():
        print(f"[WARN] Modelo no encontrado: {model_path}")
        return
    print(f"Transcribiendo con Vosk ({model_path})...")
    SetLogLevel(-1)
    model = Model(model_path)
    rec = KaldiRecognizer(model, cfg["sample_rate"])
    if rec.AcceptWaveform(audio):
        result = json.loads(rec.Result())
    else:
        result = json.loads(rec.FinalResult())
    txt = result.get("text", "").strip()
    print(f"Transcripción: {txt!r}" if txt else "(sin texto)")


# ============================ Main ============================
def print_banner(cfg: dict, model_path: str) -> None:
    print("=" * 60)
    print("   Dictation Vosk (offline, espanol)")
    print("=" * 60)
    print(f"   Modelo : {model_path}")
    print(f"   Hotkey : {cfg['hotkey']}  (toggle)")
    print(f"   Salir  : {cfg['quit_hotkey']}")
    print(f"   Config : {CONFIG_PATH}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Dictado por voz offline con Vosk")
    parser.add_argument("--test-mic", action="store_true", help="Probar microfono")
    parser.add_argument("--list-devices", action="store_true", help="Listar mics")
    parser.add_argument("--set-hotkey", metavar="HOTKEY", help="Cambiar hotkey")
    parser.add_argument("--set-model", metavar="PATH", help="Cambiar ruta del modelo")
    parser.add_argument("--show-config", action="store_true")
    args = parser.parse_args()

    cfg = load_config()
    if args.show_config:
        print(json.dumps(cfg, indent=2, ensure_ascii=False))
        return
    if args.list_devices:
        list_devices()
        return
    if args.set_hotkey:
        cfg["hotkey"] = args.set_hotkey
        save_config(cfg)
        print(f"Hotkey cambiada a: {args.set_hotkey}")
        return
    if args.set_model:
        cfg["model_path"] = args.set_model
        save_config(cfg)
        print(f"Modelo: {args.set_model}")
        return
    if args.test_mic:
        test_mic(cfg)
        return

    # Asegurar modelo
    model_path = cfg["model_path"]
    if not Path(model_path).is_dir():
        alt = find_model()
        if alt:
            model_path = alt
            cfg["model_path"] = alt
            save_config(cfg)
        else:
            print(f"[ERROR] Modelo no encontrado: {model_path}")
            print("Descarga desde https://alphacephei.com/vosk/models")
            print("  Ejemplo (espanol pequeno):")
            print("    https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip")
            print(f"Y extrae en: {Path(model_path).parent}")
            return

    print_banner(cfg, model_path)
    print("Cargando modelo Vosk (primera vez puede tardar 5-10s)...")
    SetLogLevel(-1)
    try:
        model = Model(model_path)
    except Exception as e:
        print(f"[ERROR] No se pudo cargar el modelo: {e}")
        return
    print("Modelo cargado OK.\n")
    print(f"  >> Pulsa [{cfg['hotkey']}] para empezar/detener")
    print(f"  >> Pulsa [{cfg['quit_hotkey']}] para salir")
    print()

    # Atajos globales
    keyboard.add_hotkey(cfg["hotkey"], lambda: toggle(cfg, model))
    keyboard.add_hotkey(cfg["quit_hotkey"],
                        lambda: (print("\n[EXIT] Cerrando...", flush=True), sys.exit(0)))

    try:
        keyboard.wait()
    except KeyboardInterrupt:
        print("\n[EXIT] Ctrl+C - Cerrando")


if __name__ == "__main__":
    main()
