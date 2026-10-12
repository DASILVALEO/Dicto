@echo off
REM ===========================================================================
REM  voz-a-texto - Instalador automatico para Windows 10/11
REM  Compatible con: Windows 10 LTSC, 11, cualquier CPU (incluso Sandy Bridge)
REM ===========================================================================
setlocal EnableDelayedExpansion
set DIR=%~dp0
echo ===========================================================
echo   INSTALADOR voz-a-texto (MiniMax + Vosk offline)
echo ===========================================================
echo.

REM 1) Verificar Python
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python no esta instalado.
    echo Descargalo desde https://www.python.org/downloads/
    echo MARCA "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)
python --version
echo.

REM 2) Instalar dependencias pip
echo Instalando dependencias...
python -m pip install --upgrade pip --quiet
python -m pip install -r "%DIR%requirements.txt" --quiet
if errorlevel 1 (
    echo [ERROR] Fallo instalando dependencias pip.
    pause
    exit /b 1
)
echo Dependencias OK.
echo.

REM 3) Preguntar API key de MiniMax
echo ===========================================================
echo   CONFIGURACION
echo ===========================================================
set /p MINIMAX_KEY="Pega tu MiniMax API key (sk-cp-...): "
if defined MINIMAX_KEY (
    python "%DIR%voice_dictation.py" --set-key "!MINIMAX_KEY!"
    echo API key de MiniMax guardada.
) else (
    echo Sin API key. Puedes dictar con Vosk offline.
)
echo.

REM 4) Crear acceso directo en escritorio
set SHORTCUT=%USERPROFILE%\Desktop\Dictado por Voz (MiniMax).lnk
echo Creando acceso directo en escritorio...
(
    echo Set WshShell = CreateObject("WScript.Shell"^)
    echo Set fso = CreateObject("Scripting.FileSystemObject"^)
    echo sPath = Replace(WScript.ScriptFullName, WScript.ScriptName, ""^)
    echo WshShell.CurrentDirectory = sPath
    echo Set shortcut = WshShell.CreateShortcut("%SHORTCUT%"^)
    echo shortcut.TargetPath = "%DIR%start_dictation_silent.vbs"
    echo shortcut.WorkingDirectory = "%DIR%"
    echo shortcut.IconLocation = "shell32.dll,238"
    echo shortcut.Description = "Dictado por voz (MiniMax nube + Vosk offline). Hotkey: Alt Gr"
    echo shortcut.Save
) > "%TEMP%\create_shortcut.vbs"
cscript //NoLogo "%TEMP%\create_shortcut.vbs"
del "%TEMP%\create_shortcut.vbs"
echo Acceso directo creado.
echo.

REM 5) Preguntar auto-inicio
set /p AUTOSTART="Iniciar automaticamente con Windows? (s/n): "
if /i "!AUTOSTART!"=="s" (
    reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DictationVoz" /t REG_SZ /d ""%DIR%watchdog_dictation.bat"" /f >nul
    echo Auto-inicio configurado.
) else (
    echo Sin auto-inicio. Lanza desde el acceso directo cuando quieras.
)

echo.
echo ===========================================================
echo   INSTALACION COMPLETA
echo ===========================================================
echo.
echo 1. Doble-click en "Dictado por Voz (MiniMax)" en tu escritorio
echo 2. Espera 5 segundos (carga)
echo 3. Pulsa Alt Gr (Alt derecha) para empezar a dictar
echo 4. Pulsa Alt Gr otra vez para parar y pegar
echo.
echo Para salir: edita .dictation_config.json quit_hotkey (default Ctrl+Alt+Q)
echo.
pause
