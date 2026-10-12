# voz-a-texto

Aplicación de dictado por voz para Windows que escribe donde esté el cursor.

## Características

- **MiniMax STT** (nube): alta calidad, soporta español, rápido. Requiere API key.
- **Vosk** (offline): funciona sin internet, modelo en español, sin API key.
- **Hotkey global**: `Alt Gr` (configurable) para empezar/terminar dictado.
- **Overlay visual**: barra flotante con cronómetro + VU meter de micrófono.
- **Auto-paste**: el texto transcrito aparece donde esté el cursor.
- **Watchdog**: la app se reinicia automáticamente si falla (cada 3 min).

## Requisitos

- Windows 10 / 11 (probado en Windows 10 LTSC 19044)
- Python 3.10 o superior
- Micrófono funcional

## Instalación rápida

1. Tener Python instalado (https://www.python.org/downloads/, marcar "Add to PATH")
2. Doble-click en `install.bat`
3. Pegar tu API key de MiniMax cuando lo pida
4. Listo — doble-click en el acceso directo "Dictado por Voz (MiniMax)" del escritorio

## Configuración interactiva (GUI)

Hay un **panel de configuración** con interfaz gráfica:

- Doble-click en el acceso directo "Configurador voz-a-texto" del escritorio
- O ejecutar: `pythonw configurador.pyw`

Permite:
- Ver y cambiar la API key de cualquier proveedor (MiniMax, Groq, OpenAI)
- Probar la conexión con un botón
- Cambiar la hotkey de dictado
- Cambiar el idioma
- Activar/desactivar auto-paste
- Ver el estado actual (proceso, auto-inicio, etc.)
- Reiniciar el watchdog sin reiniciar Windows

## Uso

1. **Abre cualquier app** (Word, navegador, VS Code, Excel, Bloc de notas)
2. **Pon el cursor** donde quieras escribir
3. **Pulsa `Alt Gr`** (Alt derecha) una vez — aparece la barrita verde/roja
4. **Habla en español** — verás las barras moverse según tu volumen
5. **Pulsa `Alt Gr`** otra vez — el texto se pega donde está el cursor

## Cambiar la API key

Si rotás tu API key o querés cambiar de proveedor, abrí el **Configurador** (acceso directo del escritorio). La nueva key se guarda al instante. El watchdog se reinicia automáticamente para tomar los cambios.

## Configuración

Edita `~/.dictation_config.json` (en tu carpeta de usuario):

| Campo | Valores | Default |
|---|---|---|
| `provider` | `minimax` \| `groq` \| `openai` | `minimax` |
| `minimax_api_key` | tu API key | (vacío) |
| `language` | `es`, `en`, `""` (auto) | `es` |
| `hotkey` | tecla o combinación | `alt gr` |
| `quit_hotkey` | tecla o combinación | `ctrl+alt+q` |
| `auto_paste` | `true` / `false` | `true` |

## Hotkeys admitidos

- Teclas simples: `alt gr`, `f12`, `insert`, `pause`, `right alt`, `right ctrl`
- Combinaciones: `ctrl+shift+space`, `ctrl+alt+r`, `f9`+`f10`, etc.

## Archivos

- `voice_dictation.py` — script principal (cloud: MiniMax, Groq, OpenAI)
- `dictation_vosk.py` — alternativo offline (Vosk)
- `overlay.py` — barra visual flotante
- `configurador.py` / `configurador.pyw` — panel GUI de configuración
- `configurador_silent.vbs` — launcher sin consola del configurador
- `watchdog_dictation.bat` — reinicia la app si muere
- `start_dictation_silent.vbs` — launcher sin consola
- `install.bat` — instalador para PC nueva
- `requirements.txt` — dependencias Python

## Crear API key de MiniMax

1. Ir a https://platform.minimax.io
2. Sign in
3. Click "Create API Key" en API Keys
4. Copiar y pegar en `install.bat` o en `~/.dictation_config.json`

## Compatibilidad con CPUs antiguas

- Funciona en CPUs SIN AVX2 (Sandy Bridge 2011, Ivy Bridge 2012, etc.)
- NO usa Whisper local (sí usa cloud con MiniMax o Vosk local)
