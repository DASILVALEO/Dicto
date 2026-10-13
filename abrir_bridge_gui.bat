@echo off
REM AI Office Bridge - Launcher (modo GUI)
setlocal
set DIR=C:\Users\USUARIO\Desktop\app\consultas\voz-a-texto
cd /d "%DIR%"
start "" pythonw ai_office_bridge_gui.py
exit
