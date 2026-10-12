$shell = New-Object -ComObject WScript.Shell
$desk = [Environment]::GetFolderPath("Desktop")
$dir = "C:\Users\USUARIO\Desktop\app\consultas"

# Acceso directo principal: Dictado con MiniMax
$lnk = Join-Path $desk "Dictado MiniMax (Nube Espanol).lnk"
Remove-Item -LiteralPath $lnk -Force -ErrorAction SilentlyContinue
$s = $shell.CreateShortcut($lnk)
$s.TargetPath = "C:\Windows\System32\wscript.exe"
$s.Arguments = "`"$dir\start_dictation_silent.vbs`""
$s.WorkingDirectory = $dir
$s.IconLocation = "C:\Windows\System32\shell32.dll,238"
$s.Description = "Dictado por voz usando tu cuenta MiniMax (espanol, nube, rapido). Hotkey: Ctrl+Shift+Space"
$s.Save()
Write-Output "Acceso directo creado: $lnk"

# Verificacion
$cfg = Get-Content "$env:USERPROFILE\.dictation_config.json" -Raw | ConvertFrom-Json
Write-Output ""
Write-Output "=== Configuracion actual ==="
Write-Output ("Provider: " + $cfg.provider)
Write-Output ("API key guardada: " + ($(if ($cfg.minimax_api_key) { "SI (longitud " + $cfg.minimax_api_key.Length + ")" } else { "NO" })))
Write-Output ("Hotkey: " + $cfg.hotkey)
Write-Output ("Idioma: " + $cfg.language)

Write-Output ""
Write-Output "Todo listo. Probalo."
