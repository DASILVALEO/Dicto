@echo off
REM ===========================================================================
REM  Dicto - Instalador (elige entre Python embebido o del sistema)
REM  Compatible con: Windows 10 LTSC, 11, cualquier CPU
REM ===========================================================================
setlocal EnableDelayedExpansion
set DIR=%~dp0
set HAS_EMBEDDED=0
if exist "%DIR%python\python.exe" set HAS_EMBEDDED=1

echo ===========================================================
echo   INSTALADOR Dicto
echo ===========================================================
echo.
echo   Que tipo de Python queres usar?
echo.
if %HAS_EMBEDDED% equ 1 (
    echo   [1] Python embebido ^(incluido en este ZIP, no necesita nada mas^)
) else (
    echo   [1] (No disponible - el ZIP actual no incluye Python embebido^)
)
echo   [2] Python del sistema ^(ya instalado en tu PC, requiere Python 3.10+^)
echo   [3] Salir
echo.
set /p OPT="Elige [1/2/3]: "

if "%OPT%"=="3" exit /b 0

if "%OPT%"=="1" (
    if %HAS_EMBEDDED% equ 0 (
        echo [ERROR] Este ZIP no incluye Python embebido.
        echo Descarga el ZIP "Dicto-completo.zip" o instala Python del sistema.
        pause
        exit /b 1
    )
    set PYEXE=%DIR%python\python.exe
    set PIPEXE=%DIR%python\python.exe -m pip
    set PY_MODE=EMBEBIDO
) else if "%OPT%"=="2" (
    where python >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python no esta instalado.
        echo Descargalo desde https://www.python.org/downloads/
        echo ^("Add Python to PATH" durante la instalacion^)
        pause
        exit /b 1
    )
    set PYEXE=python
    set PIPEXE=python -m pip
    set PY_MODE=SISTEMA
) else (
    echo Opcion invalida.
    pause
    exit /b 1
)

echo.
echo ===========================================================
echo   Instalando con Python %PY_MODE%
echo ===========================================================
echo.
!PYEXE! --version
echo.

REM 1) Instalar dependencias
echo [1/4] Instalando dependencias...
!PIPEXE! install --quiet keyboard sounddevice requests pyperclip numpy Pillow mss vosk
if errorlevel 1 (
    echo [ERROR] Fallo instalando dependencias.
    pause
    exit /b 1
)
echo Dependencias OK.
echo.

REM 2) Configurar API key
echo [2/4] Configuracion
echo ===========================================================
set /p MINIMAX_KEY="Pega tu MiniMax API key (sk-cp-...): "
if defined MINIMAX_KEY (
    !PYEXE! "%DIR%voice_dictation.py" --set-key "!MINIMAX_KEY!"
    echo API key de MiniMax guardada.
) else (
    echo Sin API key. Puedes usar Vosk offline ^(español sin internet^).
)
echo.

REM 3) Accesos directos
echo [3/4] Creando accesos directos en escritorio...

set SHORTCUT1=%USERPROFILE%\Desktop\Dicto - Dictado por Voz.lnk
(
    echo Set WshShell = CreateObject("WScript.Shell"^)
    echo sPath = Replace(WScript.ScriptFullName, WScript.ScriptName, ""^)
    echo WshShell.CurrentDirectory = sPath
    echo Set shortcut = WshShell.CreateShortcut("%SHORTCUT1%"^)
    echo shortcut.TargetPath = "%DIR%start_dictation_silent.vbs"
    echo shortcut.WorkingDirectory = "%DIR%"
    echo shortcut.IconLocation = "shell32.dll,238"
    echo shortcut.Description = "Dicto - Dictado por voz. Hotkey: Alt Gr"
    echo shortcut.Save
) > "%TEMP%\create_sc1.vbs"
cscript //NoLogo "%TEMP%\create_sc1.vbs"
del "%TEMP%\create_sc1.vbs"

set SHORTCUT2=%USERPROFILE%\Desktop\Dicto - Configurador.lnk
(
    echo Set WshShell = CreateObject("WScript.Shell"^)
    echo sPath = Replace(WScript.ScriptFullName, WScript.ScriptName, ""^)
    echo WshShell.CurrentDirectory = sPath
    echo Set shortcut = WshShell.CreateShortcut("%SHORTCUT2%"^)
    echo shortcut.TargetPath = "%DIR%configurador_silent.vbs"
    echo shortcut.WorkingDirectory = "%DIR%"
    echo shortcut.IconLocation = "shell32.dll,21"
    echo shortcut.Description = "Dicto - Configurador: API keys, hotkey, idioma"
    echo shortcut.Save
) > "%TEMP%\create_sc2.vbs"
cscript //NoLogo "%TEMP%\create_sc2.vbs"
del "%TEMP%\create_sc2.vbs"

echo Accesos directos creados.
echo.

REM 4) Auto-inicio opcional
echo [4/4] Inicio automatico
set /p AUTOSTART="Iniciar automaticamente con Windows? (s/n): "
if /i "!AUTOSTART!"=="s" (
    reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "Dicto" /t REG_SZ /d "\"%DIR%watchdog_dictation.bat\"" /f >nul
    echo Auto-inicio configurado.
) else (
    echo Sin auto-inicio. Lanza desde el acceso directo.
)

echo.
echo ===========================================================
echo   INSTALACION COMPLETA
echo ===========================================================
echo.
echo  Python usado: %PY_MODE%
echo.
echo  1. Doble-click en "Dicto - Dictado por Voz" del escritorio
echo  2. Espera 5 segundos ^(carga^)
echo  3. Pulsa Alt Gr para dictar
echo  4. Pulsa Alt Gr otra vez para parar y pegar
echo.
echo  Para salir: edita .dictation_config.json quit_hotkey
echo.
pause
