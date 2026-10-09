# Registers (or updates) the Windows scheduled task that runs the daily
# flood forecast. Run once:  powershell -ExecutionPolicy Bypass -File scripts\register_daily_flood_forecast.ps1
#
# 08:30 every day: after CWC's standard 08:00 gauge reading, early enough to
# be useful that day. If the machine was off or asleep at 08:30 the task runs
# as soon as it is next available, so a day is only lost if the machine stays
# off all day. Runs as the logged-in user (no stored password), so it needs
# that user signed in.
#
# Remove with:  Unregister-ScheduledTask -TaskName "FloodSense daily forecast" -Confirm:$false

$Root = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $Root "scripts\run_daily_flood_forecast.ps1"
$Name = "FloodSense daily forecast"

$action = New-ScheduledTaskAction -Execute "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
    -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Runner`"" `
    -WorkingDirectory $Root
$trigger = New-ScheduledTaskTrigger -Daily -At "08:30"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive

Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trigger -Settings $settings `
    -Principal $principal -Description "Flood forecast: live rain + river gauges, logged and self-checked (LandSlideFlood)" `
    -Force | Out-Null
Get-ScheduledTask -TaskName $Name | Select-Object TaskName, State

