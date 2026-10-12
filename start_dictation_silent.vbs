' =========================================================================
' Voice Dictation - Launcher sin consola (usa Python embebido si existe)
' =========================================================================
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
scriptPath = Replace(WScript.ScriptFullName, WScript.ScriptName, "")

' Detectar Python: primero embebido, luego sistema
embeddedPy = scriptPath & "python\pythonw.exe"
If FSO.FileExists(embeddedPy) Then
    pyExe = embeddedPy
    envPath = scriptPath & "python\Lib\site-packages"
    WshShell.Environment("PROCESS")("PYTHONPATH") = envPath
Else
    pyExe = "pythonw.exe"
End If

WshShell.CurrentDirectory = scriptPath
WshShell.Run """" & pyExe & """ """ & scriptPath & "voice_dictation.py""", 0, False
