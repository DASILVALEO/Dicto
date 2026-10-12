@echo off
REM ===========================================================================
REM Watchdog robusto: mantiene voice_dictation.py vivo y lo reinicia
REM periodicamente (cada 10 min) para evitar hooks rotos tras suspension.
REM ===========================================================================
setlocal EnableDelayedExpansion
set DIR=%~dp0
set SCRIPT=%DIR%voice_dictation.py
set LOG=%DIR%watchdog.log
REM Intervalo entre reinicios preventivos (en segundos). 180 = 3 min
set RESTART_INTERVAL=180

echo [%date% %time%] Watchdog robusto iniciado > "%LOG%"

:loop
echo [%date% %time%] Lanzando %SCRIPT% >> "%LOG%"
cd /d "%DIR%"
start /b "" pythonw.exe "%SCRIPT%"
set PID_HOT=
REM Espera RESTART_INTERVAL segundos, pero mata el proceso a la mitad para forzar refresh
REM Esto evita hooks rotos despues de suspension/hibernacion.
timeout /t %RESTART_INTERVAL% /nobreak >nul
echo [%date% %time%] Reinicio preventivo (cada %RESTART_INTERVAL%s) >> "%LOG%"
taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq %SCRIPT%" 2>>"%LOG%" >nul
taskkill /F /IM pythonw.exe 2>>"%LOG%" >nul
timeout /t 2 /nobreak >nul
goto loop

