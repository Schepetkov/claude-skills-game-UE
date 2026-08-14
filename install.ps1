<#
.SYNOPSIS
    Installs the skills in this repo into Claude Code's user-level skills directory.

.DESCRIPTION
    By default each skill is linked (Windows directory junction — no admin rights
    required), so `git pull` in this repo updates the installed skills everywhere.
    Use -Copy for independent copies that won't track this repo.

.PARAMETER Skills
    Install only the named skills. Default: all of them.

.PARAMETER Copy
    Copy instead of link.

.PARAMETER Target
    Destination skills directory. Default: ~/.claude/skills

.PARAMETER Force
    Replace existing entries with the same name without asking.

.EXAMPLE
    .\install.ps1
    .\install.ps1 -Skills ue-networking,ue-performance
    .\install.ps1 -Copy -Target .\.claude\skills
#>
[CmdletBinding()]
param(
    [string[]]$Skills,
    [switch]$Copy,
    [string]$Target = (Join-Path $HOME ".claude\skills"),
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$sourceRoot = Join-Path $PSScriptRoot 'skills'
if (-not (Test-Path $sourceRoot)) {
    throw "No 'skills' directory next to install.ps1 - run this from the cloned repo."
}

$available = Get-ChildItem -Directory $sourceRoot | Select-Object -ExpandProperty Name

if ($Skills) {
    $unknown = $Skills | Where-Object { $available -notcontains $_ }
    if ($unknown) {
        throw "Unknown skill(s): $($unknown -join ', ')`nAvailable: $($available -join ', ')"
    }
    $selected = $Skills
} else {
    $selected = $available
}

if (-not (Test-Path $Target)) {
    New-Item -ItemType Directory -Force -Path $Target | Out-Null
    Write-Host "Created $Target"
}

$mode = if ($Copy) { 'copy' } else { 'junction' }
Write-Host "Installing $($selected.Count) skill(s) into $Target ($mode)`n"

$installed = 0
$skipped   = 0

foreach ($name in $selected) {
    $src = Join-Path $sourceRoot $name
    $dst = Join-Path $Target $name

    if (Test-Path $dst) {
        if (-not $Force) {
            $existing = Get-Item $dst -Force
            $isLink = $null -ne $existing.LinkType
            $detail = if ($isLink) { "$($existing.LinkType) -> $($existing.Target)" } else { "directory" }
            Write-Host "  ? $name already exists ($detail)" -ForegroundColor Yellow
            $answer = Read-Host "    Replace it? [y/N]"
            if ($answer -notmatch '^[Yy]') {
                Write-Host "    skipped" -ForegroundColor DarkGray
                $skipped++
                continue
            }
        }
        # Remove-Item on a junction removes the link, not the target contents.
        Remove-Item $dst -Recurse -Force
    }

    if ($Copy) {
        Copy-Item -Recurse -Force $src $dst
        Write-Host "  + $name (copied)" -ForegroundColor Green
    } else {
        New-Item -ItemType Junction -Path $dst -Target $src | Out-Null
        Write-Host "  + $name (junction)" -ForegroundColor Green
    }
    $installed++
}

Write-Host ""
Write-Host "Installed $installed skill(s)$(if ($skipped) { ", skipped $skipped" })." -ForegroundColor Cyan
Write-Host "Run /skills in Claude Code to verify they are listed."
if (-not $Copy) {
    Write-Host "Linked, not copied - 'git pull' in this repo updates them in place." -ForegroundColor DarkGray
}
