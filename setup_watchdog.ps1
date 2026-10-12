# Configura watchdog de voice dictation en Task Scheduler
$dir = "C:\Users\USUARIO\Desktop\app\consultas"
$batPath = "$dir\watchdog_dictation.bat"
$taskName = "Dictation Watchdog"

# Eliminar tarea previa si existe
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction -Execute $batPath -WorkingDirectory $dir
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -DontStopOnIdleEnd `
    -StartWhenAvailable `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -RunLevel Highest `
    -Description "Mantiene voice_dictation.py vivo (auto-restart tras suspension, hibernacion o crash)"

Write-Output "Tarea '$taskName' creada en Task Scheduler"
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State, @{N='LastRun';E={$_.LastRunTime}} | Format-List
