' =========================================================================
' dictation_vosk - Launcher sin consola
' =========================================================================
Set WshShell = CreateObject("WScript.Shell")
scriptPath = Replace(WScript.ScriptFullName, WScript.ScriptName, "")
WshShell.CurrentDirectory = scriptPath
WshShell.Run "pythonw.exe """ & scriptPath & "dictation_vosk.py""", 0, False
