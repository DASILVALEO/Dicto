' =========================================================================
' Voice Dictation - Launcher sin consola (segundo plano, doble click)
' =========================================================================
Set WshShell = CreateObject("WScript.Shell")
scriptPath = Replace(WScript.ScriptFullName, WScript.ScriptName, "")
WshShell.CurrentDirectory = scriptPath
WshShell.Run "pythonw.exe """ & scriptPath & "voice_dictation.py""", 0, False
