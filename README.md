# ðŸŽ¤ Dicto

> **Tu voz. Cualquier app. En un click.**

App de **dictado por voz** que escribe donde estÃ© el cursor. Funciona en **Word, Excel, navegador, VS Code, chat, cualquier app de Windows**. Open source, gratis, pensado para correr en PCs con pocos recursos.

![Status](https://img.shields.io/badge/Status-Active-success)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)
![RAM](https://img.shields.io/badge/RAM%20mÃ­nima-4%20GB-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)
![Stars](https://img.shields.io/github/stars/DASILVALEO/Dicto?style=social)

## ðŸ“¥ Download (elige uno)

| Archivo | TamaÃ±o | DescripciÃ³n |
|---|---|---|
| **[Dicto-completo-v1.0.0.zip](https://github.com/DASILVALEO/Dicto/releases/latest)** | **58 MB** | âœ… Recomendado. Incluye Python 3.12 + todas las dependencias. No necesitas instalar nada mÃ¡s. |
| [Dicto-ligero-v1.0.0.zip](https://github.com/DASILVALEO/Dicto/releases/latest) | 380 KB | Solo cÃ³digo fuente. Requiere Python 3.10+ ya instalado. Descarga mÃ¡s rÃ¡pida. |

---

## âœ¨ Â¿Por quÃ© Dicto?

Las apps de dictado actuales tienen un problema: asumen que tienes una PC moderna. La realidad es que millones de personas dictan desde laptops con 4 GB de RAM, CPUs de 2011, sin internet confiable.

**Dicto estÃ¡ diseÃ±ado para correr donde otros no pueden.**

| CaracterÃ­stica | Detalle |
|---|---|
| ðŸ§  **IA de verdad** | MiniMax/IA (nube) o Vosk (offline) â€” ambos en espaÃ±ol nativo |
| ðŸ’¾ **Solo 4 GB RAM** | No necesitas 8-16 GB como Dragon o Wispr |
| ðŸ¢ **CPU antigua OK** | Funciona en Sandy Bridge 2011, Ivy Bridge 2012 (sin AVX2) |
| ðŸŒ **Online u Offline** | Nube para mejor calidad, offline para privacidad |
| ðŸ”“ **Open source** | MIT â€” usa, modifica, comparte |
| ðŸ’° **Gratis** | Sin suscripciÃ³n, sin telemetrÃ­a, sin cuentas obligatorias |
| âŒ¨ï¸ **Hotkey global** | Una tecla dicta en cualquier app |
| ðŸŽ¤ **VU meter** | Ves el nivel de tu voz en tiempo real |
| ðŸªŸ **Multi-app** | Word, Excel, navegador, VS Code, chat, donde sea |

---

## ðŸŽ¯ Demo

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ â—  â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘  3s         â”‚  â† Overlay flotante
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
    â†‘
    VU meter verde en vivo + cronÃ³metro

[Windows]  [Word]  [Excel]  [VSCode]  [Chrome]  [Telegram]  [Discord]
       â†“        â†“       â†“        â†“         â†“           â†“          â†“
      [Texto aparece donde estÃ¡ el cursor]    â† Funciona en TODAS
```

---

## ðŸ–¼ï¸ Configurador

Doble-click en **"Configurador Dicto"** del escritorio. Panel con 3 pestaÃ±as:

![Configurador](docs/configurador-screenshot.png)

### PestaÃ±as disponibles

| PestaÃ±a | QuÃ© hace |
|---|---|
| ðŸ”‘ **API Keys** | Configura MiniMax/IA, Groq, OpenAI o Vosk. BotÃ³n "Probar conexiÃ³n" por proveedor |
| âš™ï¸ **Comportamiento** | Hotkey, idioma, auto-paste |
| ðŸ“Š **Estado** | Ver proceso, auto-inicio, reiniciar watchdog, abrir config JSON |

---

## ðŸš€ Quick start (60 segundos)

```powershell
# 1. Instala Python 3.10+ (marca "Add to PATH"): https://python.org/downloads
# 2. Descarga Dicto (botÃ³n verde "Code" â†’ Download ZIP) o clona:
git clone https://github.com/DASILVALEO/Dicto.git
cd Dicto

# 3. Doble-click en install.bat
# 4. Pega tu API key de MiniMax/IA cuando lo pida
# 5. Listo. Abre Word, pulsa Alt Gr, habla ðŸŽ¤
```

**Â¿No tienes cuenta de MiniMax/IA?** Usa **Vosk offline** â€” funciona sin internet y sin API key (dicata en espaÃ±ol sin mÃ¡s).

---

## ðŸ“¦ Requisitos

| | MÃ­nimo | Recomendado |
|---|---|---|
| **OS** | Windows 10 (1809+) | Windows 10/11 LTSC |
| **RAM** | **4 GB** âœ… | 8 GB+ |
| **CPU** | Cualquier x86_64 (incluso Sandy Bridge 2011) | Moderno (Haswell+ para Vosk rÃ¡pido) |
| **Disco** | 200 MB | 500 MB |
| **Internet** | Solo si usas nube (MiniMax/IA, Groq, OpenAI) | No necesario con Vosk |
| **MicrÃ³fono** | Cualquiera | Integrado o USB |

> ðŸ§ª **Probado en**: MacBook Air Sandy Bridge (i5-2557M, 4GB RAM, Win 10 LTSC vÃ­a Boot Camp). Funciona perfectamente.

---

## ðŸ¤– Proveedores de transcripciÃ³n

Dicto soporta mÃºltiples proveedores. Cambia entre ellos cuando quieras desde el Configurador.

### â˜ï¸ Nube (mejor calidad)

| Proveedor | Calidad | Costo | Setup |
|---|---|---|---|
| **MiniMax/IA** | â­â­â­â­â­ | Free tier generoso | https://platform.minimax.io |
| **Groq** | â­â­â­â­â­ | Free tier | https://console.groq.com/keys |
| **OpenAI** | â­â­â­â­â­ | ~$0.006/min (1Â¢/min) | https://platform.openai.com |

### ðŸŒ‘ Offline (sin internet, gratis)

| Proveedor | Calidad | Costo | Modelo |
|---|---|---|---|
| **Vosk** | â­â­â­â­ | Gratis | 57 MB, espaÃ±ol nativo |

---

## ðŸŽ® CÃ³mo se usa

1. **Abre cualquier app** (Word, navegador, chat, editor de cÃ³digo, Excel, Bloc de notas...)
2. **Pon el cursor** donde quieras escribir
3. **Pulsa `Alt Gr`** (Alt derecha) â€” una vez
4. **Aparece una barrita flotante** ðŸŽ¤ con VU meter en vivo
5. **Habla en espaÃ±ol**
6. **Pulsa `Alt Gr`** otra vez â€” el texto se pega donde estÃ¡ el cursor âœ¨

### Atajos incluidos

| Atajo | AcciÃ³n |
|---|---|
| `Alt Gr` (mantener o pulsar) | Empezar/terminar dictado |
| `Ctrl + Alt + Q` | Salir de la app |

Personalizables desde el **Configurador**.

---

## ðŸ—ï¸ Arquitectura

```
[Tecla Alt Gr] â”€â”€â–º [keyboard.hook] â”€â”€â–º [sounddevice]
                                              â”‚
                                              â–¼
                                  [WAV 16kHz mono]
                                              â”‚
                          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                          â–¼                                  â–¼
                  [API nube (MiniMax/IA)]            [Vosk local]
                          â”‚                                  â”‚
                          â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                         â–¼
                                  [texto transcrito]
                                         â”‚
                                         â–¼
                            [pyperclip + Ctrl+V]
                                         â”‚
                                         â–¼
                              [texto en el cursor] âœ“

[Overlay Tkinter] â—„â”€â”€â”€â”€ estado + VU meter en vivo
[Watchdog .bat]   â—„â”€â”€â”€â”€ reinicia la app cada 3 min
```

**~200 lÃ­neas** de cÃ³digo Python. Sin Electron, sin Tauri, sin Chromium. Pura Python + Windows nativo.

---

## ðŸ”§ Troubleshooting

**El micro no se abre** â†’ Verifica que el micrÃ³fono predeterminado funcione en ConfiguraciÃ³n de Windows > Sonido > Entrada.

**MiniMax/IA devuelve error** â†’ Tu API key expirÃ³. Abre el **Configurador** y pega la nueva.

**La hotkey no responde** â†’ Si usas Mac con Boot Camp, presiona **Alt derecha** (no izquierda). Si sigue sin ir, prueba `f12` o `right ctrl` desde el Configurador.

**La app no inicia al prender la PC** â†’ Abre el **Configurador â†’ Estado** para verificar el auto-inicio.

---

## ðŸŒŸ Â¿Por quÃ© lo hice?

La primera vez que probÃ© apps de dictado en mi MacBook Air del 2011 (4 GB RAM, Sandy Bridge), todas fallaron. SpeakoFlow crasheaba, whisper-local no cargaba, SayIt requerÃ­a DLLs faltantes.

Luego descubrÃ­ que necesitaba CPU con AVX2 (2017+) y 8+ GB de RAM. Pero muchos usuarios no tienen eso.

**Dicto es para ellos.** Y tambiÃ©n para mÃ­.

---

## ðŸ¤ Contribuir

Pull requests bienvenidos. Ãreas abiertas:
- Soporte para mÃ¡s idiomas en Vosk
- CancelaciÃ³n de ruido (RNNoise)
- Icono en system tray para config rÃ¡pido
- Auto-detecciÃ³n de contexto (chat vs editor)
- Empaquetado como `.exe` standalone con PyInstaller

---

## ðŸ“„ Licencia

MIT â€” usa, modifica, redistribuye libremente. Si haces algo cool con esto, contame.

---

## ðŸ™ Inspirado en

- [Wispr Flow](https://wispr.com) â€” UX pulida
- [Dragon](https://nuance.com/dragon) â€” dictado profesional
- [Superwhisper](https://superwhisper.com) â€” simplicidad
- [Talon](https://talonvoice.com) â€” open source
- [Vosk](https://alphacephei.com/vosk) â€” motor ASR offline

---

## â­ Dale una estrella

Si Dicto te ahorra tiempo, dejÃ¡ una â­ en GitHub â€” ayuda mucho a que mÃ¡s gente lo descubra.

**[â¬‡ï¸ Descarga la Ãºltima versiÃ³n](https://github.com/DASILVALEO/Dicto/releases)**


