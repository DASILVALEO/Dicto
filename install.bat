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
echo Creando accesos directos en escritorio...

REM Acceso 1: Dictado directo
set SHORTCUT1=%USERPROFILE%\\Desktop\\Dictado por Voz (MiniMax).lnk
(
    echo Set WshShell = CreateObject("WScript.Shell"^)
    echo sPath = Replace(WScript.ScriptFullName, WScript.ScriptName, ""^)
    echo WshShell.CurrentDirectory = sPath
    echo Set shortcut = WshShell.CreateShortcut("%SHORTCUT1%"^)
    echo shortcut.TargetPath = "%DIR%start_dictation_silent.vbs"
    echo shortcut.WorkingDirectory = "%DIR%"
    echo shortcut.IconLocation = "shell32.dll,238"
    echo shortcut.Description = "Dictado por voz (MiniMax nube + Vosk offline). Hotkey: Alt Gr"
    echo shortcut.Save
) > "%TEMP%\\create_shortcut1.vbs"
cscript //NoLogo "%TEMP%\\create_shortcut1.vbs"
del "%TEMP%\\create_shortcut1.vbs"

REM Acceso 2: Configurador GUI
set SHORTCUT2=%USERPROFILE%\\Desktop\\Configurador voz-a-texto.lnk
(
    echo Set WshShell = CreateObject("WScript.Shell"^)
    echo sPath = Replace(WScript.ScriptFullName, WScript.ScriptName, ""^)
    echo WshShell.CurrentDirectory = sPath
    echo Set shortcut = WshShell.CreateShortcut("%SHORTCUT2%"^)
    echo shortcut.TargetPath = "%DIR%configurador_silent.vbs"
    echo shortcut.WorkingDirectory = "%DIR%"
    echo shortcut.IconLocation = "shell32.dll,21"
    echo shortcut.Description = "Configurador voz-a-texto: API keys, hotkey, idioma, etc."
    echo shortcut.Save
) > "%TEMP%\\create_shortcut2.vbs"
cscript //NoLogo "%TEMP%\\create_shortcut2.vbs"
del "%TEMP%\\create_shortcut2.vbs"

echo Accesos directos creados.
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
