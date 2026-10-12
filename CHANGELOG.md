# Changelog

All notable changes to **Dicto** will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project follows [Semantic Versioning](https://semver.org/).

## [1.0.1] - 2026-10-12

### Fixed
- **Critical: Duplicate watchdog race condition** - Two `watchdog_dictation.bat` instances were running simultaneously, each killing the other's `pythonw.exe` process during transcription, causing ~50% transcription failures. Now: only 1 watchdog runs at a time.
- **Performance: Reduced transcription delay** - `min_duration_seconds` lowered from 0.3s to 0.1s. Initial transcription response is now ~2-3 sec instead of ~3-4 sec.

### Verified
- 3 consecutive dictation tests passed 100% on MacBook Air Sandy Bridge (i5-2557M, 4GB RAM, Windows 10 LTSC via Boot Camp).
- Hotkey `Alt Gr` (right Alt on Mac) responds instantly.
- Auto-paste to cursor works in any app.

## [1.0.0] - 2026-10-12

### Initial Public Release

#### Features
- Global hotkey dictation (`Alt Gr` by default) - works in any Windows app
- 4 transcription providers:
  - **MiniMax/IA** (default) - cloud, Spanish native, fast
  - **Groq** - cloud, free tier
  - **OpenAI Whisper** - cloud, paid
  - **Vosk** - offline, no internet required
- Floating overlay with live VU meter and timer
- GUI Configurator for changing API key, hotkey, language
- Watchdog that auto-restarts every 3 minutes (anti-sleep-issues)
- Optional embedded Python (no Python install needed) or system Python
- Bilingual README (English + Spanish)
- Auto-paste at cursor position

#### Technical
- ~200 lines of Python core code
- ~150 MB installed (with embedded Python + all dependencies)
- 4 GB RAM minimum
- Runs on Sandy Bridge 2011 CPUs (no AVX2 required)
- MIT License

#### Repository
- https://github.com/DASILVALEO/Dicto
- Public on initial release, made private on 2026-10-12 for security audit.
- Topics: voice-to-text, speech-recognition, dictation, windows, python, minimax, whisper, vosk, offline-first, accessibility, productivity, ai, asr
