Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class W {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
  [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
}
"@

$h = (Get-Process -Name "sayit" -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq "SayIt" } | Select-Object -First 1 -ExpandProperty MainWindowHandle)
if ($h -ne $null -and $h -ne [IntPtr]::Zero) {
  [W]::ShowWindow($h, 9) | Out-Null
  [W]::SetForegroundWindow($h) | Out-Null
  [W]::BringWindowToTop($h) | Out-Null
  Write-Output "SayIt ventana traida al frente"
}

# Crear acceso directo en escritorio
$shell = New-Object -ComObject WScript.Shell
$desk = [Environment]::GetFolderPath("Desktop")
$lnk = Join-Path $desk "SayIt - Dictado por Voz (Groq).lnk"
Remove-Item -LiteralPath $lnk -Force -ErrorAction SilentlyContinue

$s = $shell.CreateShortcut($lnk)
$s.TargetPath = "$env:LOCALAPPDATA\SayIt\sayit.exe"
$s.WorkingDirectory = "$env:LOCALAPPDATA\SayIt"
$s.IconLocation = "$env:LOCALAPPDATA\SayIt\sayit.exe,0"
$s.Description = "SayIt - Dictado por voz open source. Hotkey configurable. Soporta Groq (gratis), OpenAI, etc."
$s.Save()
Write-Output "Acceso directo creado: $lnk"

# Habilitar auto-inicio via registro
$runKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$appName = "SayIt"
if (-not (Get-ItemProperty -Path $runKey -Name $appName -ErrorAction SilentlyContinue)) {
  $exe = "$env:LOCALAPPDATA\SayIt\sayit.exe"
  New-ItemProperty -Path $runKey -Name $appName -Value "`"$exe`"" -PropertyType String -Force | Out-Null
  Write-Output "Auto-inicio configurado en HKCU\...\Run"
} else {
  Write-Output "Auto-inicio ya estaba configurado"
}

Write-Output ""
Write-Output "=== ESTADO FINAL ==="
Get-Process -Name "sayit" -ErrorAction SilentlyContinue | Select-Object Id, MainWindowTitle, @{N='WSMB';E={[math]::Round($_.WorkingSet64/1MB,1)}}, StartTime | Format-Table -AutoSize
