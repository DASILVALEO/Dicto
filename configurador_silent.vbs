' =========================================================================
' Configurador voz-a-texto - Launcher sin consola
' =========================================================================
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
scriptPath = Replace(WScript.ScriptFullName, WScript.ScriptName, "")

embeddedPy = scriptPath & "python\pythonw.exe"
If FSO.FileExists(embeddedPy) Then
    pyExe = embeddedPy
    WshShell.Environment("PROCESS")("PYTHONPATH") = scriptPath & "python\Lib\site-packages"
Else
    pyExe = "pythonw.exe"
End If

WshShell.CurrentDirectory = scriptPath
WshShell.Run """" & pyExe & """ """ & scriptPath & "configurador.py""", 0, False
