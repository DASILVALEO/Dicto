@echo off
REM dictation_vosk - Launcher en primer plano
cd /d "%~dp0"
python dictation_vosk.py %*
