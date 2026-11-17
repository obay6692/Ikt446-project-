<#
.SYNOPSIS
  Start/stop the Oslo Bysykkel pipeline with one command.

.EXAMPLE
  .\start up               # setup (if needed) + prepare data + validation run, in background
  .\start up -Phase test   # same, but the final held-out 2026 test run
  .\start status           # is it running? last log lines
  .\start logs             # follow the log live (Ctrl+C stops following, not the run)
  .\start down             # stop the running pipeline
  .\start down -Clean      # stop and delete generated data/processed + outputs
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet("up", "down", "status", "logs", "run")]
    [string]$Command = "status",
    [ValidateSet("validation", "test")]
    [string]$Phase = "validation",
    [switch]$Clean,
    [switch]$Foreground
)

# "Continue", not "Stop": Windows PowerShell 5.1 turns any stderr line from a native
# program (python warnings, pip notices) into an error. Failures are detected via
# $LASTEXITCODE instead.
$ErrorActionPreference = "Continue"
$Root = $PSScriptRoot
$Venv = Join-Path $Root ".venv"
$Py = Join-Path $Venv "Scripts\python.exe"
$PidFile = Join-Path $Root ".run.pid"
$LogFile = Join-Path $Root "outputs\run.log"

function Get-RunningProcess {
    if (-not (Test-Path $PidFile)) { return $null }
    $id = (Get-Content $PidFile -Raw).Trim()
    $proc = Get-Process -Id $id -ErrorAction SilentlyContinue
    if ($null -eq $proc) { Remove-Item $PidFile -Force; return $null }
    return $proc
}

function Invoke-Step([string]$Title, [string[]]$PyArgs) {
    Write-Host "`n=== $Title ===" -ForegroundColor Cyan
    # -u: unbuffered, so progress shows up in the log immediately.
    # cmd /c merges stderr into stdout as plain text (avoids PS 5.1 NativeCommandError records).
    $argLine = ($PyArgs | ForEach-Object { if ($_ -match '\s') { "`"$_`"" } else { $_ } }) -join " "
    & cmd /c "`"$Py`" -u $argLine 2>&1"
    if ($LASTEXITCODE -ne 0) { throw "$Title failed (exit code $LASTEXITCODE)" }
}

# The actual pipeline. 'up' launches this in a background process; it can also run directly.
function Invoke-Pipeline {
    Set-Location $Root
    if (-not (Test-Path $Py)) {
        Write-Host "=== Creating virtual environment (Python 3.13) ===" -ForegroundColor Cyan
        & cmd /c "py -3.13 -m venv `"$Venv`" 2>&1"
        if ($LASTEXITCODE -ne 0) { throw "Could not create .venv; is Python 3.13 installed? (py -0)" }
    }
    & cmd /c "`"$Py`" -c `"import numpy, pandas, sklearn, matplotlib, joblib, torch`" >nul 2>&1"
    if ($LASTEXITCODE -ne 0) {
        $pipBusy = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
            Where-Object { $_.CommandLine -match 'pip install' }
        if ($pipBusy) { throw "Another 'pip install' is still running; wait for it to finish, then run '.\start up' again." }
        Invoke-Step "Installing requirements" @("-m", "pip", "install", "-r", "requirements.txt")
    }
    if (-not (Test-Path (Join-Path $Root "data\raw\2026\09.csv"))) {
        Invoke-Step "Extracting dataset zip" @("extract_dataset.py")
    }
    if (-not (Test-Path (Join-Path $Root "data\processed\hourly_demand.csv"))) {
        Invoke-Step "Preparing hourly data" @("prepare_data.py")
    }
    Invoke-Step "Running experiments (phase: $Phase)" @("run_experiments.py", "--phase", $Phase)
    Write-Host "`nDONE. Results in outputs\$Phase\" -ForegroundColor Green
}

switch ($Command) {
    "run" {
        # Internal: executed by 'up' in the background (or with -Foreground).
        try { Invoke-Pipeline } catch { Write-Host "ERROR: $_" -ForegroundColor Red; exit 1 }
        finally { if (Test-Path $PidFile) { Remove-Item $PidFile -Force -ErrorAction SilentlyContinue } }
    }

    "up" {
        if ($Phase -eq "test") {
            Write-Host "NOTE: test phase = final 2026 evaluation. Run it once, after freezing settings." -ForegroundColor Yellow
        }
        if ($Foreground) {
            & $PSCommandPath run -Phase $Phase
            return
        }
        $running = Get-RunningProcess
        if ($running) { Write-Host "Already running (PID $($running.Id)). Use '.\start down' first."; return }
        New-Item -ItemType Directory -Force (Split-Path $LogFile) | Out-Null
        # Out-File -Encoding utf8 (Tee-Object in PS 5.1 would write UTF-16).
        $cmd = "& '$PSCommandPath' run -Phase $Phase *>&1 | ForEach-Object { `"`$_`" } | Out-File -FilePath '$LogFile' -Encoding utf8"
        $proc = Start-Process powershell -WindowStyle Hidden -PassThru -WorkingDirectory $Root `
            -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $cmd)
        Set-Content $PidFile $proc.Id
        Write-Host "Started pipeline (phase: $Phase, PID $($proc.Id))." -ForegroundColor Green
        Write-Host "Log: outputs\run.log   Follow: .\start logs   Stop: .\start down"
    }

    "down" {
        $running = Get-RunningProcess
        if ($running) {
            # /T kills the whole tree (powershell -> python), /F forces it.
            & taskkill /PID $running.Id /T /F | Out-Null
            Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped pipeline (PID $($running.Id))." -ForegroundColor Yellow
        } else {
            Write-Host "Nothing is running."
        }
        if ($Clean) {
            Get-ChildItem (Join-Path $Root "data\processed") -Exclude ".gitkeep" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
            Get-ChildItem (Join-Path $Root "outputs") -Exclude ".gitkeep" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
            Write-Host "Removed generated files in data\processed and outputs (raw CSVs and .venv kept)."
        }
    }

    "status" {
        $running = Get-RunningProcess
        if ($running) { Write-Host "RUNNING (PID $($running.Id), started $($running.StartTime))" -ForegroundColor Green }
        else { Write-Host "Not running." }
        if (Test-Path $LogFile) { Write-Host "`n--- last lines of outputs\run.log ---"; Get-Content $LogFile -Tail 10 }
    }

    "logs" {
        if (-not (Test-Path $LogFile)) { Write-Host "No log yet. Start with: .\start up"; return }
        Get-Content $LogFile -Tail 30 -Wait
    }
}
