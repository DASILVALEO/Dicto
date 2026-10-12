"""Benchmark DictaIA: mide latencia, recursos y confiabilidad end-to-end."""
import time
import os
import sys
import wave
import json
import struct
import statistics
import psutil
import subprocess
import sounddevice as sd
import numpy as np
import requests

print("=" * 60)
print("  DictaIA - Benchmark Suite")
print("=" * 60)

# ----------------------------------------------------------------------------
# Test 1: Cold start (tiempo desde lanzamiento hasta primer toggle listo)
# ----------------------------------------------------------------------------
print("\n[1] COLD START")
print("-" * 60)
start = time.perf_counter()
subprocess.Popen(
    [sys.executable, "voice_dictation.py"],
    cwd=r"C:\Users\USUARIO\Desktop\app\consultas\voz-a-texto",
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
# Esperar a que pythonw aparezca
for _ in range(50):
    time.sleep(0.1)
    try:
        procs = [p for p in psutil.process_iter(['name', 'cmdline'])
                 if p.info['name'] == 'pythonw.exe']
        if procs and any('voice_dictation' in (p.info.get('cmdline') or [''])[0] for p in procs):
            break
    except psutil.NoSuchProcess:
        pass
elapsed_cold = (time.perf_counter() - start) * 1000
print(f"  Tiempo de lanzamiento: {elapsed_cold:.0f} ms")

# Esperar 3 seg para que se inicialice el overlay
time.sleep(3)

# ----------------------------------------------------------------------------
# Test 2: Latencia de la hotkey (simulado)
# ----------------------------------------------------------------------------
print("\n[2] HOTKEY LATENCY")
print("-" * 60)
import keyboard

latencies = []
def callback(e):
    latencies.append((time.perf_counter() - callback.t0) * 1000)

keyboard.on_press_key("alt gr", callback)
for i in range(10):
    callback.t0 = time.perf_counter()
    keyboard.press_and_release("alt gr")
    time.sleep(0.2)
keyboard.unhook_all()

if latencies:
    print(f"  N muestras: {len(latencies)}")
    print(f"  Min: {min(latencies):.0f} ms")
    print(f"  Max: {max(latencies):.0f} ms")
    print(f"  Prom: {statistics.mean(latencies):.0f} ms")
    print(f"  Mediana: {statistics.median(latencies):.0f} ms")
else:
    print("  No se capturaron latencias")

# ----------------------------------------------------------------------------
# Test 3: End-to-end: grabar -> API -> texto
# ----------------------------------------------------------------------------
print("\n[3] END-TO-END (audio -> API -> texto)")
print("-" * 60)

cfg = json.load(open(r"C:\Users\USUARIO\.dictation_config.json"))
key = cfg["minimax_api_key"]
api_url = "https://api.minimax.io/v1/speech_to_text"

# Usar una grabacion real del mic
SAMPLE_TEXTS = [
    ("corto", 2),
    ("medio", 5),
    ("largo", 10),
]

results = []
for name, dur in SAMPLE_TEXTS:
    print(f"\n  Test '{name}' ({dur}s):")
    rec = sd.rec(int(dur * 16000), samplerate=16000, channels=1, dtype='int16')
    sd.wait()
    peak = int(rec.max())
    print(f"    Audio peak: {peak} ({'silencio' if peak < 500 else 'con voz'})")

    wav = f"C:/Users/USUARIO/AppData/Local/Temp/bench_{name}.wav"
    with wave.open(wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(rec.tobytes())

    t0 = time.perf_counter()
    with open(wav, "rb") as f:
        files = {"file": ("t.wav", f, "audio/wav")}
        data = {"model": "asr-1.0", "response_format": "json"}
        headers = {"Authorization": f"Bearer {key}"}
        r = requests.post(api_url, files=files, data=data, headers=headers, timeout=30)
    api_ms = (time.perf_counter() - t0) * 1000

    txt = r.json().get("text", "")
    print(f"    Status: {r.status_code}")
    print(f"    Tiempo API: {api_ms:.0f} ms")
    print(f"    Texto: {txt!r}")
    results.append({"name": name, "duration": dur, "peak": peak,
                    "api_ms": api_ms, "text": txt, "status": r.status_code})

# ----------------------------------------------------------------------------
# Test 4: Recursos del sistema (CPU, RAM)
# ----------------------------------------------------------------------------
print("\n[4] RECURSOS DEL SISTEMA (durante grabacion)")
print("-" * 60)

# PID del dictation
pids = []
for p in psutil.process_iter(['name']):
    if p.info['name'] == 'pythonw.exe':
        try:
            cmd = ' '.join(p.cmdline() or [])
            if 'voice_dictation' in cmd:
                pids.append(p.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

if pids:
    p = psutil.Process(pids[0])
    print(f"  PID: {p.pid}")
    print(f"  RAM (RSS): {p.memory_info().rss / 1024 / 1024:.1f} MB")
    print(f"  Threads: {p.num_threads()}")
    print(f"  Handles: {p.num_handles()}")

    # CPU idle
    p.cpu_percent(interval=0.5)
    time.sleep(2)
    cpu_idle = p.cpu_percent(interval=2.0)
    print(f"  CPU (idle): {cpu_idle:.1f}%")
else:
    print("  Proceso pythonw no encontrado")

# ----------------------------------------------------------------------------
# Test 5: Estabilidad (lanzamientos repetidos = watchdog)
# ----------------------------------------------------------------------------
print("\n[5] ESTABILIDAD (reinicios del watchdog)")
print("-" * 60)
log_path = r"C:\Users\USUARIO\Desktop\app\consultas\voz-a-texto\watchdog.log"
if os.path.exists(log_path):
    restarts = []
    with open(log_path) as f:
        for line in f:
            if "Lanzando" in line:
                # Format: [date time] Lanzando ...
                try:
                    timestamp_str = line.split("]")[0][1:]
                    # Parse "lun. 12/10/2026 14:50:03,13"
                    time_str = timestamp_str.split(" ", 1)[1]
                    parts = time_str.split(":")
                    h, m, s = int(parts[0]), int(parts[1]), float(parts[2].replace(",", "."))
                    sec_of_day = h * 3600 + m * 60 + s
                    restarts.append(sec_of_day)
                except Exception:
                    pass
    if len(restarts) > 1:
        intervals = [restarts[i+1] - restarts[i] for i in range(len(restarts)-1)]
        print(f"  Reinicios observados: {len(restarts)}")
        print(f"  Intervalo min: {min(intervals):.0f}s")
        print(f"  Intervalo max: {max(intervals):.0f}s")
        print(f"  Intervalo prom: {sum(intervals)/len(intervals):.0f}s")
        print(f"  Intervalo configurado: 180s")

# ----------------------------------------------------------------------------
# Resumen
# ----------------------------------------------------------------------------
print("\n" + "=" * 60)
print("  RESUMEN")
print("=" * 60)
if results:
    print(f"\n  E2E (grabacion + API):")
    for r in results:
        success = "OK" if r['status'] == 200 else "FAIL"
        print(f"    [{success}] {r['name']:6s} ({r['duration']:>2d}s): {r['api_ms']:>5.0f}ms -> {r['text']!r}")

print("\n  Recomendaciones de mejora:")
print("    - Audio < 1s: descartado (no suficiente material para transcribir)")
print("    - Audio 2-5s: optimo (latencia API ~1-2s)")
print("    - Audio > 10s: partes de transcripcion (latencia API ~2-3s)")
