# Run a long command in the background and wait for it in one blocking call. Windows PowerShell 5.1 and PowerShell 7.
#
#   bg.ps1 [--root DIR] start [--name N] [--cwd D] [--on-done CMD] -- <command...>
#   bg.ps1 [--root DIR] wait <id> [--max S] [--tail N]
#   bg.ps1 [--root DIR] status <id> [--tail N]
#
# Same interface as bg.py and bg.sh: `start` returns {id, root, log, wait} at once; `wait` blocks inside this script until
# the job exits, its supervisor dies or --max seconds pass, prints {id, state, exit_code, elapsed_seconds, log, tail} and
# exits with the job's code (3 while running, 4 when lost). Run it as
#   powershell -ExecutionPolicy Bypass -File <dir>\bg.ps1 start --name tests -- <command>
# Jobs live under $env:ORBYN_BG_ROOT or a per-user temp folder. Keep this file ASCII: 5.1 reads it as ANSI.

$ErrorActionPreference = 'Stop'
$RUNNING = 3
$LOST = 4
$SelfPath = $MyInvocation.MyCommand.Path
$Utf8 = New-Object System.Text.UTF8Encoding($false)
$Epoch = New-Object DateTime 1970, 1, 1, 0, 0, 0, ([DateTimeKind]::Utc)

function Fail([string]$Message, [int]$Code = 1) {
    [Console]::Error.WriteLine('bg: ' + $Message)
    exit $Code
}

function Now { [int64][Math]::Floor(([DateTime]::UtcNow - $Epoch).TotalSeconds) }

# Write atomically: temp file, then rename over the target.
function Write-Atomic([string]$Path, $Data) {
    $temp = $Path + '.tmp'
    $text = (ConvertTo-Json -InputObject $Data -Depth 6) + "`n"
    [System.IO.File]::WriteAllText($temp, $text, $Utf8)
    if (Test-Path -LiteralPath $Path) { [System.IO.File]::Replace($temp, $Path, $null) }
    else { [System.IO.File]::Move($temp, $Path) }
}

function Read-Json([string]$Path) {
    try { return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json) } catch { return $null }
}

function Get-DefaultRoot {
    if ($env:ORBYN_BG_ROOT) { return $env:ORBYN_BG_ROOT }
    $user = $env:USERNAME
    if (-not $user) { $user = $env:USER }
    if (-not $user) { $user = 'user' }
    return (Join-Path ([System.IO.Path]::GetTempPath()) ('orbyn-bg-' + $user))
}

function Test-PidAlive($ProcessId) {
    if (-not $ProcessId) { return $false }
    return [bool](Get-Process -Id ([int]$ProcessId) -ErrorAction SilentlyContinue)
}

# Quote one argument for a Windows command line (CommandLineToArgvW rules).
function Quote-Arg([string]$Arg) {
    if ($Arg.Length -gt 0 -and $Arg -notmatch '[\s"]') { return $Arg }
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append('"')
    $slashes = 0
    foreach ($c in $Arg.ToCharArray()) {
        if ($c -eq [char]92) { $slashes++; continue }
        if ($c -eq [char]34) { [void]$sb.Append([string]::new([char]92, $slashes * 2 + 1)); [void]$sb.Append('"') }
        else { if ($slashes -gt 0) { [void]$sb.Append([string]::new([char]92, $slashes)) }; [void]$sb.Append($c) }
        $slashes = 0
    }
    if ($slashes -gt 0) { [void]$sb.Append([string]::new([char]92, $slashes * 2)) }
    [void]$sb.Append('"')
    return $sb.ToString()
}

function Get-JobDir([string]$Root, [string]$Job) {
    if (-not $Job -or $Job.Contains('/') -or $Job.Contains('\') -or $Job.StartsWith('.') -or
        -not (Test-Path -LiteralPath (Join-Path (Join-Path $Root $Job) 'job.json'))) {
        Fail ("no job '" + $Job + "' under " + $Root)
    }
    return (Join-Path $Root $Job)
}

# The job's state: done (with its exit code), running, lost or starting.
function Get-JobState([string]$Dir) {
    $job = Read-Json (Join-Path $Dir 'job.json')
    $created = 0
    if ($job -and $job.created) { $created = [int64]$job.created }
    $result = @{ state = 'lost'; exit_code = $null; ended = $null; created = $created }
    $done = Read-Json (Join-Path $Dir 'exit.json')
    if ($done) { $result.state = 'done'; $result.exit_code = [int]$done.exit_code; $result.ended = [int64]$done.ended; return $result }
    $sup = Read-Json (Join-Path $Dir 'supervisor.json')
    if (-not $sup) {
        if ((Now) - $created -lt 30) { $result.state = 'starting' }
        return $result
    }
    if (Test-PidAlive $sup.pid) { $result.state = 'running'; return $result }
    $done = Read-Json (Join-Path $Dir 'exit.json') # finished between the two reads
    if ($done) { $result.state = 'done'; $result.exit_code = [int]$done.exit_code; $result.ended = [int64]$done.ended }
    return $result
}

function Get-LogTail([string]$Dir, [int]$Lines) {
    $log = Join-Path $Dir 'output.log'
    if ($Lines -le 0 -or -not (Test-Path -LiteralPath $log)) { return '' }
    try {
        $stream = New-Object System.IO.FileStream($log, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        $reader = New-Object System.IO.StreamReader($stream, $Utf8)
        $text = $reader.ReadToEnd()
        $reader.Dispose()
    } catch { return '' }
    $all = @($text -split "\r?\n")
    if ($all.Count -gt 0 -and $all[$all.Count - 1] -eq '') { $all = $all[0..($all.Count - 2)] }
    if ($all.Count -eq 0) { return '' }
    if ($all.Count -gt $Lines) { $all = $all[($all.Count - $Lines)..($all.Count - 1)] }
    return ($all -join "`n")
}

# Print the JSON report and return the exit code to use.
function Write-Report([string]$Dir, $Info, [int]$Lines) {
    $end = $Info.ended
    if (-not $end) { $end = Now }
    $elapsed = [Math]::Max(0, $end - $Info.created)
    $report = [ordered]@{
        id = (Split-Path -Leaf $Dir); state = $Info.state; exit_code = $Info.exit_code; elapsed_seconds = $elapsed
        log = (Join-Path $Dir 'output.log'); tail = (Get-LogTail $Dir $Lines)
    }
    Write-Output (ConvertTo-Json -InputObject $report -Depth 4)
    if ($Info.state -eq 'done') {
        if ($Info.exit_code -ge 0 -and $Info.exit_code -lt 256) { return [int]$Info.exit_code }
        return 1
    }
    if ($Info.state -eq 'lost') { return $LOST }
    return $RUNNING
}

# Starts a program with stdout and stderr merged into one live log; the C# part avoids PowerShell event plumbing.
function Initialize-Runner {
    Add-Type -TypeDefinition @'
using System;
using System.Diagnostics;
using System.IO;
using System.Text;
public class BgRun {
    Process p; StreamWriter w; readonly object gate = new object();
    public int Start(string file, string args, string cwd, string log) {
        ProcessStartInfo psi = new ProcessStartInfo(file, args);
        psi.WorkingDirectory = cwd;
        psi.UseShellExecute = false;
        psi.CreateNoWindow = true;
        psi.RedirectStandardInput = true;
        psi.RedirectStandardOutput = true;
        psi.RedirectStandardError = true;
        psi.StandardOutputEncoding = new UTF8Encoding(false);
        psi.StandardErrorEncoding = new UTF8Encoding(false);
        w = new StreamWriter(new FileStream(log, FileMode.Append, FileAccess.Write, FileShare.ReadWrite), new UTF8Encoding(false));
        w.AutoFlush = true;
        p = new Process();
        p.StartInfo = psi;
        p.OutputDataReceived += Line;
        p.ErrorDataReceived += Line;
        try { p.Start(); } catch { w.Dispose(); throw; }
        p.StandardInput.Close();
        p.BeginOutputReadLine();
        p.BeginErrorReadLine();
        return p.Id;
    }
    void Line(object sender, DataReceivedEventArgs e) {
        if (e.Data != null) { lock (gate) { w.WriteLine(e.Data); } }
    }
    public int Wait() {
        p.WaitForExit();
        int code = p.ExitCode;
        lock (gate) { w.Dispose(); }
        return code;
    }
}
'@
}

# --- commands -------------------------------------------------------------------------------------------------

function Invoke-Start([string]$Root, [string[]]$Rest) {
    $name = ''; $cwd = ''; $onDone = ''
    $i = 0
    $command = @()
    while ($i -lt $Rest.Count) {
        $arg = $Rest[$i]
        if ($arg -eq '--') {
            if ($i + 1 -lt $Rest.Count) { $command = @($Rest[($i + 1)..($Rest.Count - 1)]) }
            break
        }
        if ($arg -eq '--name' -or $arg -eq '--cwd' -or $arg -eq '--on-done') {
            if ($i + 1 -ge $Rest.Count) { Fail ($arg + ' needs a value') }
            if ($arg -eq '--name') { $name = $Rest[$i + 1] } elseif ($arg -eq '--cwd') { $cwd = $Rest[$i + 1] } else { $onDone = $Rest[$i + 1] }
            $i += 2
            continue
        }
        if ($arg.StartsWith('-')) { Fail ('unknown option ' + $arg + ' for start') }
        $command = @($Rest[$i..($Rest.Count - 1)])
        break
    }
    if ($command.Count -eq 0) { Fail 'give the command after --' }

    New-Item -ItemType Directory -Force -Path $Root | Out-Null
    $stamp = (Get-Date).ToString('yyyyMMdd-HHmmss')
    $bytes = New-Object byte[] 3
    (New-Object System.Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes)
    $id = $stamp + '-' + (($bytes | ForEach-Object { $_.ToString('x2') }) -join '')
    if ($name) {
        $safe = $name -replace '[^A-Za-z0-9_-]', '-'
        if ($safe.Length -gt 40) { $safe = $safe.Substring(0, 40) }
        $id += '-' + $safe
    }
    $dir = Join-Path $Root $id
    New-Item -ItemType Directory -Path $dir | Out-Null
    if ($cwd) { $resolved = Resolve-Path -LiteralPath $cwd -ErrorAction SilentlyContinue; if ($resolved) { $cwd = $resolved.ProviderPath } }
    else { $cwd = (Get-Location).ProviderPath }
    $onDoneValue = $null
    if ($onDone) { $onDoneValue = $onDone }
    Write-Atomic (Join-Path $dir 'job.json') ([ordered]@{ id = $id; command = @($command); cwd = $cwd; on_done = $onDoneValue; created = (Now) })
    [System.IO.File]::WriteAllText((Join-Path $dir 'output.log'), '', $Utf8)

    $shell = (Get-Process -Id $PID).Path
    $arguments = '-NoProfile -ExecutionPolicy Bypass -File ' + (Quote-Arg $SelfPath) + ' _supervise ' + (Quote-Arg $dir)
    Start-Process -FilePath $shell -ArgumentList $arguments -WindowStyle Hidden | Out-Null

    $out = [ordered]@{ id = $id; root = $Root; log = (Join-Path $dir 'output.log'); wait = ('bg.ps1 wait ' + $id) }
    Write-Output (ConvertTo-Json -InputObject $out -Depth 3)
    exit 0
}

# Runs detached: start the command, record its exit code, then run the optional on-done command.
function Invoke-Supervise([string]$Dir) {
    $job = Read-Json (Join-Path $Dir 'job.json')
    $log = Join-Path $Dir 'output.log'
    $command = @($job.command)
    $found = Get-Command -Name $command[0] -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $found) {
        $message = 'could not start: ' + $command[0] + ' not found'
        [System.IO.File]::AppendAllText($log, 'bg: ' + $message + "`n", $Utf8)
        Write-Atomic (Join-Path $Dir 'exit.json') ([ordered]@{ exit_code = 127; ended = (Now); error = $message })
        exit 0
    }
    $file = $found.Source
    $parts = @()
    for ($k = 1; $k -lt $command.Count; $k++) { $parts += (Quote-Arg ([string]$command[$k])) }
    $argString = $parts -join ' '
    if ($file -match '\.(cmd|bat)$') {
        $argString = '/d /c "' + (Quote-Arg $file) + ' ' + $argString + '"'
        $file = $env:ComSpec
    }
    try {
        Initialize-Runner
        $runner = New-Object BgRun
        $childPid = $runner.Start($file, $argString, $job.cwd, $log)
    } catch {
        $message = 'could not start: ' + $_.Exception.Message
        [System.IO.File]::AppendAllText($log, 'bg: ' + $message + "`n", $Utf8)
        Write-Atomic (Join-Path $Dir 'exit.json') ([ordered]@{ exit_code = 127; ended = (Now); error = $message })
        exit 0
    }
    Write-Atomic (Join-Path $Dir 'supervisor.json') ([ordered]@{ pid = $PID; child_pid = $childPid; started = (Now) })
    $code = $runner.Wait()
    Write-Atomic (Join-Path $Dir 'exit.json') ([ordered]@{ exit_code = $code; ended = (Now) })
    if ($job.on_done) {
        $env:BG_JOB_ID = [string]$job.id
        $env:BG_EXIT_CODE = [string]$code
        $env:BG_LOG = $log
        $hook = '/d /s /c "' + $job.on_done + ' >> ' + (Quote-Arg (Join-Path $Dir 'on_done.log')) + ' 2>&1"'
        Start-Process -FilePath $env:ComSpec -ArgumentList $hook -WorkingDirectory $job.cwd -WindowStyle Hidden -Wait | Out-Null
    }
    exit 0
}

function Invoke-Wait([string]$Root, [string[]]$Rest, [bool]$Block) {
    if ($Rest.Count -eq 0) { Fail 'a job id is needed' }
    $job = $Rest[0]
    $max = 540.0; $lines = 40
    $i = 1
    while ($i -lt $Rest.Count) {
        $arg = $Rest[$i]
        if ($i + 1 -ge $Rest.Count) { Fail ($arg + ' needs a value') }
        if ($arg -eq '--max' -and $Block) { $max = [double]::Parse($Rest[$i + 1], [System.Globalization.CultureInfo]::InvariantCulture) }
        elseif ($arg -eq '--tail') { $lines = [int]$Rest[$i + 1] }
        else { Fail ('unknown option ' + $arg) }
        $i += 2
    }
    $dir = Get-JobDir $Root $job
    $watch = [System.Diagnostics.Stopwatch]::StartNew()
    while ($true) {
        $info = Get-JobState $dir
        if (-not $Block -or $info.state -eq 'done' -or $info.state -eq 'lost' -or $watch.Elapsed.TotalSeconds -ge $max) {
            exit (Write-Report $dir $info $lines)
        }
        Start-Sleep -Milliseconds 250
    }
}

# --- main -----------------------------------------------------------------------------------------------------

$argv = @($args | ForEach-Object { [string]$_ })
$root = Get-DefaultRoot
if ($argv.Count -ge 1 -and $argv[0] -eq '--root') {
    if ($argv.Count -lt 2) { Fail '--root needs a value' }
    $root = $argv[1]
    $argv = if ($argv.Count -gt 2) { @($argv[2..($argv.Count - 1)]) } else { @() }
}
if ($argv.Count -eq 0) { Fail 'usage: bg.ps1 [--root DIR] start|wait|status ...' 2 }
$action = $argv[0]
$rest = if ($argv.Count -gt 1) { @($argv[1..($argv.Count - 1)]) } else { @() }
switch ($action) {
    'start' { Invoke-Start $root $rest }
    'wait' { Invoke-Wait $root $rest $true }
    'status' { Invoke-Wait $root $rest $false }
    '_supervise' { Invoke-Supervise $rest[0] }
    default { Fail ("unknown action '" + $action + "' (use start, wait or status)") 2 }
}
