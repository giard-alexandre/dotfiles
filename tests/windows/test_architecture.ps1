#Requires -Version 5.1
# Behavioral guard regression; mocked CIM is not native Windows acceptance.
# Run with powershell.exe or pwsh -NoProfile -File tests/windows/test_architecture.ps1.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$oldOs = $env:OS
$oldArchitecture = $env:PROCESSOR_ARCHITECTURE

# Stop immediately after each guard, before any real platform/config/package work.
function Get-ItemProperty { throw 'PAST_ARCHITECTURE_GUARD' }
function Join-Path { throw 'PAST_ARCHITECTURE_GUARD' }
function Get-CimInstance {
    param($ClassName, $Property, $ErrorAction)
    if ($queryFails) { throw 'CIM_UNAVAILABLE' }
    foreach ($architecture in $architectures) {
        [pscustomobject]@{ Architecture = $architecture }
    }
}

try {
    $env:OS = 'Windows_NT'
    $env:PROCESSOR_ARCHITECTURE = 'AMD64'
    $cases = @(
        @{ Name = 'x64'; Values = @(9); Fails = $false; Accepted = $true },
        @{ Name = 'ARM64 under AMD64 emulation'; Values = @(12); Fails = $false; Accepted = $false },
        @{ Name = 'empty query'; Values = @(); Fails = $false; Accepted = $false },
        @{ Name = 'unknown architecture'; Values = @($null); Fails = $false; Accepted = $false },
        @{ Name = 'mixed processors'; Values = @(9, 12); Fails = $false; Accepted = $false },
        @{ Name = 'query failure'; Values = @(); Fails = $true; Accepted = $false }
    )
    foreach ($file in @('bootstrap.ps1', 'developer-tools.ps1')) {
        foreach ($case in $cases) {
            $architectures = $case.Values
            $queryFails = $case.Fails
            $failure = $null
            try { & "$root/scripts/windows/$file" } catch { $failure = $_.Exception.Message }
            if ($null -eq $failure) { throw "$file / $($case.Name): unexpected completion" }
            $accepted = $failure -eq 'PAST_ARCHITECTURE_GUARD'
            if ($accepted -ne $case.Accepted) {
                throw "$file / $($case.Name): unexpected guard result: $failure"
            }
            if (-not $accepted -and $failure -notlike '*native x64 host*' -and $failure -ne 'CIM_UNAVAILABLE') {
                throw "$file / $($case.Name): unrelated failure: $failure"
            }
            Write-Output "PASS $file / $($case.Name)"
        }
    }
} finally {
    $env:OS = $oldOs
    $env:PROCESSOR_ARCHITECTURE = $oldArchitecture
}
