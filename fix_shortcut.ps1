$shell = New-Object -ComObject WScript.Shell
$desk = [Environment]::GetFolderPath("Desktop")

# Replace the experimental shortcut with a real one
$lnkPath = Join-Path $desk "Whisper Local - Dictado por Voz (Offline).lnk"
Remove-Item -LiteralPath (Join-Path $desk "Whisper Local (experimental).lnk") -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $lnkPath -Force -ErrorAction SilentlyContinue

$s = $shell.CreateShortcut($lnkPath)
$s.TargetPath = "C:\Users\USUARIO\Desktop\app\consultas\installers\whisper-local.exe"
$s.WorkingDirectory = "C:\Users\USUARIO\Desktop\app\consultas\installers"
$s.IconLocation = "C:\Users\USUARIO\Desktop\app\consultas\installers\whisper-local.exe,0"
$s.Description = "Whisper Local - Dictado por voz 100% offline y open-source. Hotkey: Ctrl+Win"
$s.WindowStyle = 7  # Minimized (since it shows logs in console)
$s.Save()
Write-Output "Acceso directo creado: $lnkPath"

# Also enable autostart via the built-in flag
$errLog = "C:\Users\USUARIO\AppData\Local\Temp\wl_autostart.log"
Remove-Item -LiteralPath $errLog -Force -ErrorAction SilentlyContinue
Start-Process -FilePath "C:\Users\USUARIO\Desktop\app\consultas\installers\whisper-local.exe" -ArgumentList "--enable-autostart" -WindowStyle Hidden -RedirectStandardError $errLog
Start-Sleep -Seconds 3
Write-Output "Auto-inicio solicitado via --enable-autostart"

# Keep the Win+H shortcut as fallback option (in case user prefers native Windows dictation)
Write-Output ""
Get-ChildItem $desk -Filter "*.lnk" -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "Dictado|Whisper|Voz" } | Select-Object Name | Format-Table -AutoSize
