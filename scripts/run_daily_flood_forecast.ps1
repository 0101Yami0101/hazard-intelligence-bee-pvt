# Daily flood forecast: live rain + river gauges -> outlook, river chances,
# forecast log and outcome checks (scripts/model/flood_forecast_live.py).
#
# Run by the Windows scheduled task "FloodSense daily forecast" (see
# scripts/register_daily_flood_forecast.ps1). Safe to run by hand too; a
# second run on the same day replaces that day's issue in the log.
#
# Retries because every input is a free public feed (Open-Meteo, CWC, NWDP)
# and a single dropped connection should not cost a day of the track record.
# Output: logs/flood_forecast_daily/<date>.log

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\model\flood_forecast_live.py"
$LogDir = Join-Path $Root "logs\flood_forecast_daily"
$Log = Join-Path $LogDir ("{0:yyyy-MM-dd}.log" -f (Get-Date))
$Attempts = 3
$WaitMinutes = 10

New-Item -ItemType Directory -Force $LogDir | Out-Null
$env:PYTHONUTF8 = "1"
$env:LOKY_MAX_CPU_COUNT = "4"
Set-Location $Root

# Python is launched by full path and its output captured to temp files:
# this machine's PATH has no System32, so nothing may rely on cmd.exe or
# other bare command names.
$Out = Join-Path $LogDir "_stdout.tmp"
$Err = Join-Path $LogDir "_stderr.tmp"

for ($i = 1; $i -le $Attempts; $i++) {
    "=== attempt $i of $Attempts, $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===" | Out-File $Log -Append -Encoding utf8
    try {
        $p = Start-Process -FilePath $Python -ArgumentList "`"$Script`"" -WorkingDirectory $Root `
            -NoNewWindow -Wait -PassThru -RedirectStandardOutput $Out -RedirectStandardError $Err
        $code = $p.ExitCode
    } catch {
        "could not start python: $_" | Out-File $Log -Append -Encoding utf8
        $code = -1
    }
    foreach ($f in $Out, $Err) {
        if (Test-Path $f) { Get-Content $f -Encoding utf8 | Out-File $Log -Append -Encoding utf8; Remove-Item $f }
    }
    if ($code -eq 0) {
        "=== done ===" | Out-File $Log -Append -Encoding utf8
        exit 0
    }
    "=== failed (exit $code) ===" | Out-File $Log -Append -Encoding utf8
    if ($i -lt $Attempts) { Start-Sleep -Seconds (60 * $WaitMinutes) }
}
exit 1
