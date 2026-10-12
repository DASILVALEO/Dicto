' =========================================================================
' Configurador voz-a-texto - Launcher sin consola
' =========================================================================
Set WshShell = CreateObject("WScript.Shell")
scriptPath = Replace(WScript.ScriptFullName, WScript.ScriptName, "")
WshShell.CurrentDirectory = scriptPath
WshShell.Run "pythonw.exe """ & scriptPath & "configurador.py""", 0, False
