#Requires -Version 5.1
<#
Native, inspectable entry point. Default is read-only preflight.
No init, apply, remote script execution, PATH persistence or policy bypass.
Run from a reviewed local copy; see docs/WINDOWS.md.
#>
[CmdletBinding()]
param(
    [switch]$EstablishXdg,
    [switch]$InstallCore,
    [switch]$InstallDeveloperTools
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Confirm-Action([string]$Message, [string]$Expected) {
    if ((Read-Host "$Message Type '$Expected' to continue") -cne $Expected) {
        throw 'Not consented; stopped. Earlier explicitly approved actions are not rolled back.'
    }
}

function Get-NativeCommand([string]$Name) {
    $commands = @(Get-Command $Name -CommandType Application -All -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty Source -Unique)
    if ($commands.Count -gt 1) {
        throw "Multiple $Name installations on PATH: $($commands -join ', '). Resolve ownership manually; nothing is uninstalled."
    }
    if ($commands.Count -eq 1) { return $commands[0] }
    return $null
}

function Invoke-Checked([string]$Exe, [string[]]$Arguments) {
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Exe exited with $LASTEXITCODE. Stop and inspect (including reboot/policy/refusal); do not continue setup."
    }
}

if ($env:OS -ne 'Windows_NT') { throw 'Native Windows only.' }
if (-not [Environment]::Is64BitProcess -or $env:PROCESSOR_ARCHITECTURE -ne 'AMD64') {
    throw 'Use native x64 Windows PowerShell; ARM64 and emulated processes are not validated.'
}
# Query the platform, not the virtual AMD64 processor exposed to emulated apps.
# Win32_Processor.Architecture: 9 = x64, 12 = ARM64. Missing/query failures stop.
$processors = @(Get-CimInstance -ClassName Win32_Processor -Property Architecture -ErrorAction Stop)
if ($processors.Count -eq 0 -or @($processors | Where-Object { $_.Architecture -ne 9 }).Count -ne 0) {
    throw 'A native x64 host is required; ARM64/emulated or unknown hosts are not supported.'
}
$build = [int](Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').CurrentBuildNumber
if ($build -lt 22000) { throw 'This first slice targets Windows 11 x64.' }
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run as a standard user, not an elevated deployment shell.'
}
Write-Host "PowerShell $($PSVersionTable.PSVersion); execution policy: $(Get-ExecutionPolicy)"

$homePath = [Environment]::GetFolderPath('UserProfile')
if ($homePath -notmatch '^[A-Za-z]:\\' -or $homePath.TrimEnd('\') -ine $env:USERPROFILE.TrimEnd('\')) {
    throw 'Nonstandard/redirected home: stop for a reviewed path mapping.'
}
$expectedXdg = Join-Path $homePath '.config'
foreach ($scope in @('User', 'Machine', 'Process')) {
    $value = [Environment]::GetEnvironmentVariable('XDG_CONFIG_HOME', $scope)
    if ($value -and $value.Replace('/', '\').TrimEnd('\') -ine $expectedXdg) {
        throw "Conflicting $scope XDG_CONFIG_HOME=$value. Back up and reconcile application configs manually; this script will not overwrite it."
    }
}
$localData = [Environment]::GetFolderPath('LocalApplicationData')
$roamingData = [Environment]::GetFolderPath('ApplicationData')
if ($localData -ine $env:LOCALAPPDATA -or $roamingData -ine $env:APPDATA) {
    throw 'AppData environment differs from known folders; stop for manual investigation.'
}
# Do not silently hide existing native configs when switching discovery to XDG.
foreach ($legacy in @((Join-Path $roamingData 'nushell'), (Join-Path $localData 'nvim'))) {
    if (Test-Path -LiteralPath $legacy) {
        throw "Existing native configuration at $legacy. Back up and explicitly migrate/reconcile it before retrying. Do not delete runtime data."
    }
}
# Refuse known managed paths routed through junctions/symlinks. Read-only, including ancestors.
foreach ($relative in @('.config\nushell\config.nu', '.config\nushell\env.nu', '.config\git\windows.inc', '.config\mise\windows.toml', '.dotfiles\git\template.txt', '.editorconfig')) {
    $path = Join-Path $homePath $relative
    while ($path) {
        if (Test-Path -LiteralPath $path) {
            $item = Get-Item -LiteralPath $path -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Reparse point at $path. Stop for manual layout review."
            }
        }
        $path = Split-Path -Parent $path
    }
    $target = Join-Path $homePath $relative
    if (Test-Path -LiteralPath $target) { Write-Warning "Existing target: $target. Review diff and use interactive apply; never --force." }
}

if ($EstablishXdg) {
    Confirm-Action "Set user and current-process XDG_CONFIG_HOME to $expectedXdg? This affects other XDG-aware apps too." 'SET XDG'
    [Environment]::SetEnvironmentVariable('XDG_CONFIG_HOME', $expectedXdg, 'User')
    $env:XDG_CONFIG_HOME = $expectedXdg
}
if ([Environment]::GetEnvironmentVariable('XDG_CONFIG_HOME', 'User') -ine $expectedXdg -or
    $env:XDG_CONFIG_HOME -ine $expectedXdg) {
    throw 'User/process XDG_CONFIG_HOME is not established. Review and rerun with -EstablishXdg in this PowerShell process. New Terminal processes require sign-out/sign-in.'
}

# Refresh only this process from registered paths, retaining existing entries. Never setx.
if ($InstallCore -or $InstallDeveloperTools) {
    $env:PATH = @($env:PATH, [Environment]::GetEnvironmentVariable('Path', 'Machine'),
        [Environment]::GetEnvironmentVariable('Path', 'User')) -join ';'
}
$winget = Get-NativeCommand 'winget.exe'
if (-not $winget) {
    throw 'WinGet unavailable. Install/update Microsoft App Installer via Microsoft Store, sign out/in for registration, or consult Microsoft native repair instructions in docs/WINDOWS.md. No fallback manager.'
}
Invoke-Checked $winget @('--version')
$packages = @(
    @{ Id = 'Git.Git'; Exe = 'git.exe' },
    @{ Id = 'twpayne.chezmoi'; Exe = 'chezmoi.exe' },
    @{ Id = 'Nushell.Nushell'; Exe = 'nu.exe' },
    @{ Id = 'Microsoft.WindowsTerminal'; Exe = 'wt.exe' }
)
if ($InstallDeveloperTools) { $packages += @{ Id = 'jdx.mise'; Exe = 'mise.exe' } }
foreach ($package in $packages) {
    $exe = Get-NativeCommand $package.Exe
    if (-not $exe) {
        if (-not $InstallCore -and -not ($InstallDeveloperTools -and $package.Id -eq 'jdx.mise')) {
            throw "Missing $($package.Exe); review -InstallCore (or -InstallDeveloperTools for mise). No package changes made for this package."
        }
        Invoke-Checked $winget @('show', '--id', $package.Id, '--exact', '--source', 'winget')
        Confirm-Action "Review publisher, version, installer/scope, dependencies and license above. Install $($package.Id)? Installer may request UAC; refusal stops setup." "INSTALL $($package.Id)"
        # Scope is not forced: not every selected installer supports user scope.
        # Agreements stay interactive; no automatic upgrades or source changes.
        Invoke-Checked $winget @('install', '--id', $package.Id, '--exact', '--source', 'winget', '--no-upgrade')
        $env:PATH = @($env:PATH, [Environment]::GetEnvironmentVariable('Path', 'Machine'),
            [Environment]::GetEnvironmentVariable('Path', 'User')) -join ';'
        $exe = Get-NativeCommand $package.Exe
        if (-not $exe) { throw "$($package.Exe) still unavailable. Sign out/in and retry; do not install a second copy." }
    }
    if ($package.Id -eq 'jdx.mise') {
        # A singleton PATH executable is NOT evidence of package ownership. Do not
        # execute it (even --version) until registration/path provenance is reviewed.
        Invoke-Checked $winget @('list', '--id', 'jdx.mise', '--exact', '--source', 'winget')
        $digest = (Get-FileHash -Algorithm SHA256 -LiteralPath $exe).Hash.ToLowerInvariant()
        Write-Host "Resolved mise.exe: $exe`nSHA256: $digest"
        Write-Warning 'WinGet registration alone does not link this PATH file to the package. Verify this exact executable belongs to the jdx.mise installation using Installed Apps/installer location and publisher provenance. Reject portable/foreign copies; do not confirm merely because winget list succeeded.'
        Confirm-Action 'After verifying the displayed file is the registered jdx.mise installation, record ownership? This confirmation is not a signature verification.' 'CONFIRM jdx.mise OWNERSHIP'
        $receiptPath = Join-Path $localData 'mise-windows\ownership.json'
        $ancestor = $receiptPath
        while ($ancestor) {
            if ((Test-Path -LiteralPath $ancestor) -and
                ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                throw "Reparse point at $ancestor; ownership record not written."
            }
            $ancestor = Split-Path -Parent $ancestor
        }
        $null = New-Item -ItemType Directory -Force -Path (Split-Path -Parent $receiptPath)
        $receipt = @{ package = 'jdx.mise'; path = $exe; sha256 = $digest } | ConvertTo-Json
        [IO.File]::WriteAllText($receiptPath, $receipt, (New-Object Text.UTF8Encoding($false)))
    }
    Write-Host "$($package.Id): $exe (reused or installed; native version/startup gates still required)"
    if ($package.Exe -ne 'wt.exe') { Invoke-Checked $exe @('--version') }
}
Write-Host 'Preflight complete. Nothing initialized or applied. Follow docs/WINDOWS.md for explicit init, diff, dry-run, conflict review and consented apply.'
