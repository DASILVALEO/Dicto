@echo off
REM ===========================================================================
REM  Watchdog: mantiene voice_dictation.py vivo siempre
REM  Reinicia cada 3 min para evitar hooks rotos tras suspension
REM ===========================================================================
setlocal EnableDelayedExpansion
set DIR=%~dp0
set SCRIPT=%DIR%voice_dictation.py
set LOG=%DIR%watchdog.log
set RESTART_INTERVAL=180

echo [%date% %time%] Watchdog iniciado > "%LOG%"

:loop
echo [%date% %time%] Lanzando %SCRIPT% >> "%LOG%"
cd /d "%DIR%"

REM Detectar Python embebido
if exist "%DIR%python\pythonw.exe" (
    set PYEXE=%DIR%python\pythonw.exe
) else (
    set PYEXE=pythonw.exe
)
start /b "" "!PYEXE!" "%SCRIPT%"

timeout /t %RESTART_INTERVAL% /nobreak >nul
echo [%date% %time%] Reinicio preventivo >> "%LOG%"
taskkill /F /IM pythonw.exe 2>>"%LOG%" >nul
taskkill /F /IM python.exe 2>>"%LOG%" >nul
timeout /t 2 /nobreak >nul
goto loop
