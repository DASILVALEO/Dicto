# Contributing to Dicto

¡Gracias por tu interés en mejorar Dicto! Este documento te guía para empezar.

## 🚀 Setup para desarrollo

```bash
# 1. Fork y clona el repo
git clone https://github.com/TU_USUARIO/Dicto.git
cd Dicto

# 2. Crea un virtualenv (recomendado)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. Lanza el watchdog
watchdog_dictation.bat
```

## 🧪 Test rápido

Antes de hacer commit:

```bash
# Test de microfono
python voice_dictation.py --test-mic

# Test del configurador
pythonw configurador.pyw

# Genera el demo GIF
python make_demo_gif.py
```

## 📁 Estructura del proyecto

```
Dicto/
├── voice_dictation.py        # Script principal (cloud STT)
├── dictation_vosk.py         # Alternativa offline
├── overlay.py                # Widget visual Tkinter
├── configurador.py           # Panel de configuración GUI
├── watchdog_dictation.bat    # Auto-restart cada 3 min
├── install.bat               # Instalador para PC nueva
├── start_dictation_silent.vbs
├── configurador_silent.vbs
├── logo.svg, banner.svg      # Branding
├── docs/                     # Screenshots y assets
│   ├── demo.gif
│   ├── configurador-screenshot.png
│   ├── screenshot-1-grabando-word.png
│   ├── screenshot-2-procesando.png
│   ├── screenshot-3-resultado.png
│   └── screenshot-4-multi-app.png
└── README.md, README_ES.md
```

## 🎯 Áreas donde contribuir

### 🟢 Fácil (PR de 1-2 horas)
- **Más idiomas en Vosk**: descargar modelo nuevo, agregar a docs/
- **Traducciones del README**: ya tenemos ES, agregar más (pt, fr, de...)
- **Bug fixes**: revisar issues abiertos
- **Mejorar documentación**: typos, ejemplos, troubleshooting

### 🟡 Medio (PR de 1-2 días)
- **System tray icon**: agregar icono en bandeja con menú (Show config / Quit)
- **Cancelación de ruido**: integrar RNNoise via sounddevice
- **Historial de dictados**: guardar texto + audio + tiempo
- **Atajos por aplicación**: distintos hotkeys según la app en foco

### 🔴 Avanzado (PR de 1+ semana)
- **Empaquetado .exe**: usar PyInstaller para crear un solo .exe sin Python
- **Context auto-detection**: identificar si el cursor está en chat, editor, etc.
- **Wake word**: "Hey Dicto" para iniciar dictado sin hotkey
- **Streaming transcription**: ver el texto mientras hablas (como Otter.ai)

## 📐 Convenciones de código

- **Python 3.10+** (uso de type hints)
- **Líneas < 100 caracteres**
- **Funciones pequeñas** con docstrings
- **Sin dependencias innecesarias** (la app es liviana por diseño)
- **Comentarios en español** para usuarios hispanohablantes, en inglés para código

## 🔄 Proceso de Pull Request

1. Crea una rama: `git checkout -b feature/mi-feature`
2. Commit con mensaje descriptivo: `git commit -m "feat: agregu XYZ"`
3. Push: `git push origin feature/mi-feature`
4. Abre un PR en GitHub
5. Espera review (puede tardar unos días)
6. Una vez aprobado, se mergea a main

## 🐛 Reportar bugs

Abre un [issue](https://github.com/DASILVALEO/Dicto/issues) con:
- Descripción del problema
- Pasos para reproducir
- Versión de Windows y Python
- Salida de `python voice_dictation.py --test-mic`
- Screenshots si aplica

## 💬 Preguntas

¿Dudas? Abre un [Discussion](https://github.com/DASILVALEO/Dicto/discussions) en GitHub.

---

**Gracias por hacer Dicto mejor. 🎤**
