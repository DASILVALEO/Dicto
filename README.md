# 🎤 DictaIA

**Dictado por voz que escribe donde esté el cursor.**

Habla. Se escribe solo. Funciona en Word, Excel, navegador, VS Code, chat — cualquier app de Windows.

> Open source · 4 GB RAM mínimo · Compatible con PCs antiguas · Online (MiniMax/IA) u Offline (Vosk)

![Status](https://img.shields.io/badge/Status-Active-success)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)
![RAM](https://img.shields.io/badge/RAM%20mínima-4%20GB-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## ✨ ¿Por qué DictaIA?

La mayoría de apps de dictado:
- ❌ Requieren CPU moderna (AVX2+)
- ❌ Necesitan 8-16 GB de RAM
- ❌ Piden cuenta y suscripción
- ❌ Funcionan mal en PCs viejas

**DictaIA está pensado para correr donde otras no pueden**, en tu laptop vieja, en ese PC con 4GB de RAM que tienes en el rincón. Y lo hace con IA de verdad (no OCR de audio malo).

| | DictaIA | Wispr Flow | Dragon | Whisper local |
|---|---|---|---|---|
| 💰 Precio | Gratis | $15/mes | $500+ | Gratis |
| 🌐 Offline | ✅ (Vosk) | ❌ | ❌ | ✅ |
| 🐌 CPU antiguas | ✅ | ❌ | ❌ | ❌ |
| 🪟 Multi-app | ✅ | ✅ | ✅ | ❌ (solo archivos) |
| 🔓 Open source | ✅ | ❌ | ❌ | ✅ |
| 🧠 Calidad nube | ✅ (MiniMax) | ✅ | ✅ | ❌ (lento local) |
| 🛠️ Hotkey custom | ✅ | ✅ | ❌ | ❌ |

---

## 🚀 Quick start (60 segundos)

```powershell
# 1. Instala Python 3.10+ (marca "Add to PATH"): https://python.org/downloads
# 2. Clona o descarga este repo
git clone https://github.com/DASILVALEO/dictaia.git
cd dictaia

# 3. Doble-click en install.bat
# 4. Pega tu API key de MiniMax/IA cuando lo pida
# 5. Listo. Abre cualquier app y pulsa Alt Gr
```

No tienes cuenta de MiniMax/IA? Usa **Vosk offline** (español nativo, sin internet).

---

## 📦 Requisitos

| | Mínimo | Recomendado |
|---|---|---|
| **OS** | Windows 10 (1809+) | Windows 10/11 LTSC |
| **RAM** | 4 GB | 8 GB+ |
| **CPU** | Cualquier x86_64 (incluso Sandy Bridge 2011) | Moderno (Haswell+ si quieres Vosk rápido) |
| **Disco** | 200 MB | 500 MB |
| **Internet** | Solo para MiniMax/IA (opcional) | No necesario con Vosk |
| **Micrófono** | Cualquiera | Integrado o USB |

✅ **Funciona en CPUs SIN AVX2** (Sandy Bridge 2011, Ivy Bridge 2012) — a diferencia de Whisper local.

---

## 🎯 Cómo se usa

1. **Abre cualquier app** (Word, navegador, chat, editor de código, Excel, Bloc de notas...)
2. **Pon el cursor** donde quieras escribir
3. **Pulsa `Alt Gr`** (Alt derecha) una vez → aparece la barrita flotante
4. **Habla en español** — las barras verdes suben con tu voz
5. **Pulsa `Alt Gr`** otra vez → el texto se pega donde está el cursor

### Atajos incluidos

| Atajo | Acción |
|---|---|
| `Alt Gr` (mantener o pulsar) | Empezar/terminar dictado |
| `Ctrl + Alt + Q` | Salir de la app |

Configurables desde el **Configurador** (acceso directo del escritorio).

---

## 🖥️ Captura

```
  ┌────────────────────────────────────────────┐
  │ ● ████████░░░░░░░░░░░░░░░░░░░  3s         │  ← Grabando
  └────────────────────────────────────────────┘
       ↑ VU meter (verde = nivel de tu voz)
```

Overlay transparente con VU meter y cronómetro, flotando sobre cualquier app.

---

## ⚙️ Configuración (GUI)

Doble-click en **"Configurador dictaia"** del escritorio. Tres pestañas:

### 🔑 API Keys
- **MiniMax/IA** (default, recomendado — nube, alta calidad)
- **Groq** (gratis, nube)
- **OpenAI** (pago, nube)
- **Botón "Probar conexión"** para verificar cada una

### ⚙️ Comportamiento
- Hotkey (default: `alt gr`)
- Idioma (es, en, fr, de, pt, ja, zh, o vacío = auto)
- Auto-paste (pegar donde esté el cursor)

### 📊 Estado
- Ver proceso (activo/no)
- Auto-inicio en Windows
- Reiniciar watchdog
- Abrir archivo de config

La API key se guarda **solo en tu PC** (`~/.dictation_config.json`). **Nunca** se sube a GitHub.

---

## 🔌 Proveedores de transcripción

### MiniMax/IA (default, recomendado)
- **Ventajas**: Soporta español nativo, muy rápido, free tier generoso
- **Setup**: https://platform.minimax.io → API Keys → Create
- **Costo**: Free tier (con cuota mensual)

### Groq
- **Ventajas**: Whisper Large v3 ultra-rápido
- **Setup**: https://console.groq.com/keys
- **Costo**: Free tier

### OpenAI Whisper
- **Ventajas**: Calidad top de la industria
- **Setup**: https://platform.openai.com/api-keys
- **Costo**: ~$0.006/minuto (1¢ por minuto)

### Vosk (offline, sin internet)
- **Ventajas**: Sin API key, sin internet, español nativo
- **Setup**: Automático al usar `dictation_vosk.py`
- **Costo**: Gratis, modelo de 57 MB

---

## 🏗️ Arquitectura

```
[Tecla Alt Gr] → [keyboard.hook] → [sounddevice] → [API nube o Vosk]
                                              ↓
                                     [pyperclip + Ctrl+V]
                                              ↓
                                  [texto en el cursor] ✓
                                              ↓
[Overlay Tkinter] ← estado + VU meter en vivo
[Watchdog .bat]   ← reinicia la app cada 3 min
```

- **Lenguaje**: Python 3.10+ (core), VBS (launchers), BAT (watchdog), Tkinter (overlay)
- **Sin Electron, sin Tauri, sin Chromium** — pura Python + Windows nativo
- **~200 líneas** de código principal
- **0 deps nativas compiladas** — solo wheels pip

---

## 🔧 Troubleshooting

**"El micro no se abre"** → Verifica que el micrófono predeterminado funcione en Configuración de Windows > Sonido > Entrada.

**"MiniMax/IA devuelve error"** → Tu API key expiró. Abre el **Configurador** y pega la nueva.

**"La hotkey no responde"** → Si usas Mac con Boot Camp, presiona **Alt derecha** (no izquierda). Si sigue sin ir, prueba `f12` o `right ctrl` desde el Configurador.

**"La app no inicia al prender la PC"** → Abre el **Configurador → Estado → "Auto-inicio"** para verificar.

---

## 🤝 Contribuir

Pull requests bienvenidos. Áreas abiertas:
- Soporte para más idiomas en Vosk
- Mejorar la cancelación de ruido
- Interfaz con icono en system tray (config rápido)
- Auto-detección de contexto (cursor en chat vs editor)

---

## 📄 Licencia

MIT — usa, modifica, redistribuye libremente. Si haces algo cool con esto, contame.

---

## 🙏 Créditos

- [Vosk](https://alphacephei.com/vosk/) — motor ASR offline
- [MiniMax/IA](https://platform.minimax.io) — STT en la nube
- [keyboard](https://github.com/boppreh/keyboard) — global hotkey
- [sounddevice](https://python-sounddevice.readthedocs.io) — captura de audio
- Inspirado en Wispr Flow, Superwhisper, Dragon, Talon

---

**⭐ Si te sirve, dejá una estrella en GitHub — ayuda mucho.**
