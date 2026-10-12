# Contributing to Dicto

Â¡Gracias por tu interÃ©s en mejorar Dicto! Este documento te guÃ­a para empezar.

## ðŸš€ Setup para desarrollo

```bash
# 1. Fork y clona el repo
git clone https://github.com/tu_usuario/Dicto.git
cd Dicto

# 2. Crea un virtualenv (recomendado)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. Lanza el watchdog
watchdog_dictation.bat
```

## ðŸ§ª Test rÃ¡pido

Antes de hacer commit:

```bash
# Test de microfono
python voice_dictation.py --test-mic

# Test del configurador
pythonw configurador.pyw

# Genera el demo GIF
python make_demo_gif.py
```

## ðŸ“ Estructura del proyecto

```
Dicto/
â”œâ”€â”€ voice_dictation.py        # Script principal (cloud STT)
â”œâ”€â”€ dictation_vosk.py         # Alternativa offline
â”œâ”€â”€ overlay.py                # Widget visual Tkinter
â”œâ”€â”€ configurador.py           # Panel de configuraciÃ³n GUI
â”œâ”€â”€ watchdog_dictation.bat    # Auto-restart cada 3 min
â”œâ”€â”€ install.bat               # Instalador para PC nueva
â”œâ”€â”€ start_dictation_silent.vbs
â”œâ”€â”€ configurador_silent.vbs
â”œâ”€â”€ logo.svg, banner.svg      # Branding
â”œâ”€â”€ docs/                     # Screenshots y assets
â”‚   â”œâ”€â”€ demo.gif
â”‚   â”œâ”€â”€ configurador-screenshot.png
â”‚   â”œâ”€â”€ screenshot-1-grabando-word.png
â”‚   â”œâ”€â”€ screenshot-2-procesando.png
â”‚   â”œâ”€â”€ screenshot-3-resultado.png
â”‚   â””â”€â”€ screenshot-4-multi-app.png
â””â”€â”€ README.md, README_ES.md
```

## ðŸŽ¯ Ãreas donde contribuir

### ðŸŸ¢ FÃ¡cil (PR de 1-2 horas)
- **MÃ¡s idiomas en Vosk**: descargar modelo nuevo, agregar a docs/
- **Traducciones del README**: ya tenemos ES, agregar mÃ¡s (pt, fr, de...)
- **Bug fixes**: revisar issues abiertos
- **Mejorar documentaciÃ³n**: typos, ejemplos, troubleshooting

### ðŸŸ¡ Medio (PR de 1-2 dÃ­as)
- **System tray icon**: agregar icono en bandeja con menÃº (Show config / Quit)
- **CancelaciÃ³n de ruido**: integrar RNNoise via sounddevice
- **Historial de dictados**: guardar texto + audio + tiempo
- **Atajos por aplicaciÃ³n**: distintos hotkeys segÃºn la app en foco

### ðŸ”´ Avanzado (PR de 1+ semana)
- **Empaquetado .exe**: usar PyInstaller para crear un solo .exe sin Python
- **Context auto-detection**: identificar si el cursor estÃ¡ en chat, editor, etc.
- **Wake word**: "Hey Dicto" para iniciar dictado sin hotkey
- **Streaming transcription**: ver el texto mientras hablas (como Otter.ai)

## ðŸ“ Convenciones de cÃ³digo

- **Python 3.10+** (uso de type hints)
- **LÃ­neas < 100 caracteres**
- **Funciones pequeÃ±as** con docstrings
- **Sin dependencias innecesarias** (la app es liviana por diseÃ±o)
- **Comentarios en espaÃ±ol** para usuarios hispanohablantes, en inglÃ©s para cÃ³digo

## ðŸ”„ Proceso de Pull Request

1. Crea una rama: `git checkout -b feature/mi-feature`
2. Commit con mensaje descriptivo: `git commit -m "feat: agregu XYZ"`
3. Push: `git push origin feature/mi-feature`
4. Abre un PR en GitHub
5. Espera review (puede tardar unos dÃ­as)
6. Una vez aprobado, se mergea a main

## ðŸ› Reportar bugs

Abre un [issue](https://github.com/DASILVALEO/Dicto/issues) con:
- DescripciÃ³n del problema
- Pasos para reproducir
- VersiÃ³n de Windows y Python
- Salida de `python voice_dictation.py --test-mic`
- Screenshots si aplica

## ðŸ’¬ Preguntas

Â¿Dudas? Abre un [Discussion](https://github.com/DASILVALEO/Dicto/discussions) en GitHub.

---

**Gracias por hacer Dicto mejor. ðŸŽ¤**


