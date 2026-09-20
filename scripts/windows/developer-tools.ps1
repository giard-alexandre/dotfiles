#Requires -Version 5.1
<# Explicit provisioning/automation only; never dot-source from shell startup.
   The manifest is deliberately not a global mise config. No project trust needed.
#>
[CmdletBinding(DefaultParameterSetName = 'Check')]
param(
    [Parameter(ParameterSetName = 'Install')][switch]$Install,
    [Parameter(ParameterSetName = 'Run', Mandatory = $true)][string]$Run,
    [Parameter(ParameterSetName = 'Run')][string[]]$ToolArguments = @()
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Native Windows only.' }
if (-not [Environment]::Is64BitProcess -or $env:PROCESSOR_ARCHITECTURE -ne 'AMD64') {
    throw 'This tool profile requires native x64 Windows.'
}
# Match bootstrap's host check even when this runner is invoked independently.
$processors = @(Get-CimInstance -ClassName Win32_Processor -Property Architecture -ErrorAction Stop)
if ($processors.Count -eq 0 -or @($processors | Where-Object { $_.Architecture -ne 9 }).Count -ne 0) {
    throw 'A native x64 host is required; ARM64/emulated or unknown hosts are not supported.'
}
$homePath = [Environment]::GetFolderPath('UserProfile')
$configPath = Join-Path $homePath '.config\mise\windows.toml'
if ($env:XDG_CONFIG_HOME -ine (Join-Path $homePath '.config')) { throw 'Establish canonical XDG_CONFIG_HOME first.' }
# Reject inherited activation/settings instead of accidentally executing project hooks.
if (@(Get-ChildItem Env: | Where-Object { $_.Name -like 'MISE_*' }).Count) {
    throw 'Use a clean shell without MISE_* overrides/activation for this isolated tool profile.'
}
$mise = @(Get-Command mise.exe -CommandType Application -All -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty Source -Unique)
if ($mise.Count -ne 1) { throw 'Exactly one native mise.exe must be on PATH. Run bootstrap -InstallDeveloperTools; resolve duplicates manually.' }
# Compare the deployed file before installing or running anything. Version changes
# require source review + diff + consented apply, never interpreting arbitrary TOML.
$reviewed = Join-Path $PSScriptRoot '..\..\dot_config\mise\windows.toml'
if (-not (Test-Path -LiteralPath $configPath) -or
    (Get-FileHash -LiteralPath $configPath).Hash -ne (Get-FileHash -LiteralPath $reviewed).Hash) {
    throw 'Missing/different Windows manifest. Review source and target; apply the reviewed file without discarding customizations.'
}
$specs = @()
foreach ($line in (Get-Content -LiteralPath $configPath)) {
    if ($line -match '^"((?:aqua:[A-Za-z0-9_/-]+|core:bun|github:can1357/oh-my-pi))" = "([0-9]+\.[0-9]+\.[0-9]+)"$') {
        $specs += "$($Matches[1])@$($Matches[2])"
    } elseif ($line -notmatch '^\s*(#.*|\[tools\])?$') { throw "Unsupported manifest syntax: $line" }
}
if ($specs.Count -ne 5) { throw 'Expected exactly five reviewed tools.' }
$localData = [Environment]::GetFolderPath('LocalApplicationData')
if ($localData -ine $env:LOCALAPPDATA) { throw 'Unexpected LocalAppData mapping.' }
$receiptPath = Join-Path $localData 'mise-windows\ownership.json'
foreach ($managedPath in @($configPath, $receiptPath)) {
    $ancestor = $managedPath
    while ($ancestor) {
        if ((Test-Path -LiteralPath $ancestor) -and
            ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Reparse point at $ancestor. Review the tool profile layout manually."
        }
        $ancestor = Split-Path -Parent $ancestor
    }
}
# No mise code runs before this check. Receipt is an explicit human ownership
# attestation bound to path+bytes, not an inferred WinGet/signature verification.
if (-not (Test-Path -LiteralPath $receiptPath)) {
    throw 'Unconfirmed mise ownership. Run bootstrap -InstallDeveloperTools and review the registered package and resolved file.'
}
$receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
$digest = (Get-FileHash -Algorithm SHA256 -LiteralPath $mise[0]).Hash.ToLowerInvariant()
if ($receipt.package -cne 'jdx.mise' -or $receipt.path -cne $mise[0] -or $receipt.sha256 -cne $digest) {
    throw 'mise path/bytes/ownership changed. Re-run bootstrap -InstallDeveloperTools for manual ownership review; no execution permitted.'
}
# Dedicated store: never reuse an unrelated global/project mise configuration.
$settings = @{
    MISE_NO_CONFIG = '1'
    MISE_AUTO_INSTALL = '0'
    MISE_EXEC_AUTO_INSTALL = '0'
    MISE_DATA_DIR = (Join-Path $localData 'mise-windows\data')
    MISE_CACHE_DIR = (Join-Path $localData 'mise-windows\cache')
    MISE_STATE_DIR = (Join-Path $localData 'mise-windows\state')
}
function Invoke-Mise([string[]]$Arguments) {
    & $mise[0] @Arguments
    if ($LASTEXITCODE -ne 0) { throw "mise failed ($LASTEXITCODE); no fallback install or upgrade." }
}
try {
    foreach ($key in $settings.Keys) { [Environment]::SetEnvironmentVariable($key, $settings[$key], 'Process') }
    if ($Install) {
        & (Join-Path $PSScriptRoot 'bootstrap.ps1')
        if (-not $?) { throw 'Preflight failed.' }
        # Foreign PATH copies, including WinGet copies, require manual ownership review.
        foreach ($name in @('nvim.exe', 'rg.exe', 'fd.exe', 'bun.exe', 'bunx.exe', 'omp.exe', 'omp.cmd', 'omp.ps1')) {
            if (Get-Command $name -CommandType @('Application', 'ExternalScript') -ErrorAction SilentlyContinue) {
                throw "Existing $name on PATH: reconcile ownership first; nothing is uninstalled."
            }
        }
        Write-Host ($specs -join "`n")
        Write-Warning 'Inspect Installed Apps/winget list for non-PATH copies too. Only mise owns these tools.'
        if ((Read-Host 'After reviewing versions, backends and existing ownership, type INSTALL TOOLS') -cne 'INSTALL TOOLS') { throw 'Not consented.' }
        Invoke-Mise (@('install') + $specs)
    }
    # mise exec with auto-install disabled can otherwise silently fall through to
    # an unrelated PATH executable. Fail before command execution if any pin is absent.
    foreach ($spec in $specs) { $null = Invoke-Mise @('where', $spec) }
    if ($Run) {
        # Direct argv mode, never mise -c / shell string evaluation.
        Invoke-Mise (@('exec') + $specs + @('--', $Run) + $ToolArguments)
    } else {
        foreach ($name in @('nvim', 'rg', 'fd', 'bun', 'omp')) {
            Invoke-Mise (@('exec') + $specs + @('--', $name, '--version'))
        }
    }
} finally {
    foreach ($key in $settings.Keys) { [Environment]::SetEnvironmentVariable($key, $null, 'Process') }
}
