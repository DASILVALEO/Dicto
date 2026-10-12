$shell = New-Object -ComObject WScript.Shell
$desk = [Environment]::GetFolderPath("Desktop")

# Acceso directo: Configuración de Voz (dictado)
$lnk1 = Join-Path $desk "Dictado - Configurar Voz (Win+H).lnk"
$s = $shell.CreateShortcut($lnk1)
$s.TargetPath = "ms-settings:speech"
$s.WorkingDirectory = "%WINDIR%"
$s.IconLocation = "C:\Windows\System32\shell32.dll,238"
$s.Description = "Abre Configuración de Voz de Windows (donde se activa el idioma para dictado)"
$s.Save()

# Acceso directo: Ayuda Dictado Word (cualquier app)
$lnk2 = Join-Path $desk "Como usar el Dictado Win+H.lnk"
$s2 = $shell.CreateShortcut($lnk2)
$s2.TargetPath = "https://support.microsoft.com/es-es/windows/dictar-texto-con-reconocimiento-de-voz-9f9e2cd5-08a6-4a64-b1f0-aa8f7c7f3c3e"
$s2.WorkingDirectory = "%WINDIR%"
$s2.IconLocation = "C:\Windows\System32\imageres.dll,68"
$s2.Description = "Pasos para dictar con Win+H en cualquier aplicación"
$s2.Save()

# Acceso directo: Lanzar el .exe de whisper-local (por si lo quiere usar manualmente luego)
$lnk3 = Join-Path $desk "Whisper Local (experimental).lnk"
$s3 = $shell.CreateShortcut($lnk3)
$s3.TargetPath = "C:\Users\USUARIO\Desktop\app\consultas\installers\whisper-local.exe"
$s3.WorkingDirectory = "C:\Users\USUARIO\Desktop\app\consultas\installers"
$s3.IconLocation = "C:\Windows\System32\shell32.dll,237"
$s3.Description = "Lanza whisper-local (instalado pero con problemas de GUI en este equipo)"
$s3.WindowStyle = 1
$s3.Save()

Write-Output "Accesos directos creados en el escritorio:"
Get-ChildItem $desk -Filter "*.lnk" -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "Dictado|Whisper|Voz" } | Select-Object Name, Length
