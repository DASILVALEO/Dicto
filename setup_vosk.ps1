$shell = New-Object -ComObject WScript.Shell
$desk = [Environment]::GetFolderPath("Desktop")
$dir = "C:\Users\USUARIO\Desktop\app\consultas"

# Acceso directo: Dictado Vosk (offline espanol)
$lnk = Join-Path $desk "Dictado Vosk (Offline Espanol).lnk"
Remove-Item -LiteralPath $lnk -Force -ErrorAction SilentlyContinue
$s = $shell.CreateShortcut($lnk)
$s.TargetPath = "C:\Windows\System32\wscript.exe"
$s.Arguments = "`"$dir\start_vosk_silent.vbs`""
$s.WorkingDirectory = $dir
$s.IconLocation = "C:\Windows\System32\shell32.dll,238"
$s.Description = "Dictado por voz offline con Vosk (espanol). Hotkey: Ctrl+Shift+Space"
$s.Save()
Write-Output "Acceso directo creado: $lnk"

# Acceso directo: Dictado con consola (para ver logs)
$lnk2 = Join-Path $desk "Dictado Vosk (con Consola).lnk"
Remove-Item -LiteralPath $lnk2 -Force -ErrorAction SilentlyContinue
$s2 = $shell.CreateShortcut($lnk2)
$s2.TargetPath = "$dir\start_vosk.bat"
$s2.WorkingDirectory = $dir
$s2.IconLocation = "C:\Windows\System32\cmd.exe,0"
$s2.Description = "Dictado Vosk con ventana de consola (para ver transcripcion)"
$s2.Save()
Write-Output "Acceso directo creado: $lnk2"

# Auto-inicio
$runKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$appName = "DictationVosk"
$command = "wscript.exe `"$dir\start_vosk_silent.vbs`""
if (-not (Get-ItemProperty -Path $runKey -Name $appName -ErrorAction SilentlyContinue)) {
  New-ItemProperty -Path $runKey -Name $appName -Value $command -PropertyType String -Force | Out-Null
  Write-Output "Auto-inicio configurado: $appName"
} else {
  Write-Output "Auto-inicio ya estaba configurado"
}

Write-Output ""
Write-Output "=== Verificacion final ==="
Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq "" -and $_.CPU -lt 0.1 } | Select-Object Id | Format-Table -AutoSize
Write-Output "Accesos directos:"
Get-ChildItem $desk -Filter "Dictado Vosk*.lnk" -ErrorAction SilentlyContinue | Select-Object Name | Format-Table -AutoSize
