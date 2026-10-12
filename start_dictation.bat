@echo off
REM =====================================================================
REM   Voice Dictation - Launcher en primer plano (muestra consola)
REM =====================================================================
cd /d "%~dp0"
python voice_dictation.py %*
