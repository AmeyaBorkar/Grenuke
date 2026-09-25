<#
One-time setup for a clone of the Grenuke repo (Windows PowerShell 5.1+ / PowerShell 7).
Usage (from the repo root):
    powershell -ExecutionPolicy Bypass -File scripts/setup.ps1          # git config + hooks only
    powershell -ExecutionPolicy Bypass -File scripts/setup.ps1 -Venv    # also create .venv and install the package
#>
param([switch]$Venv)
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# Enforcement hooks (commit-msg / pre-commit / pre-push) live in .githooks
git config core.hooksPath .githooks
git config pull.rebase true
git config fetch.prune true
git config rebase.autoStash true
git config core.autocrlf false   # line endings are handled by .gitattributes

$name = git config user.name
$email = git config user.email
if (-not $name -or -not $email) {
    Write-Warning "Set your git identity first: git config --global user.name 'Your Name'; git config --global user.email 'you@example.com'"
}

if ($Venv) {
    if (-not (Test-Path ".venv")) { python -m venv .venv }
    & .\.venv\Scripts\python.exe -m pip install --upgrade pip
    & .\.venv\Scripts\python.exe -m pip install -e "code/business_entity_resolution[dev]"
    Write-Host "Venv ready. Activate with: .\.venv\Scripts\Activate.ps1"
    Write-Host "Full pinned env: pip install -r code/business_entity_resolution/requirements.txt"
}

Write-Host "core.hooksPath = $(git config core.hooksPath)"
Write-Host "Put the Unstop dataset in student_resource/dataset/{train,test}/ (git-ignored; never commit it)."
Write-Host "Next: read CONTRIBUTING.md, docs/TEAM.md, docs/ROADMAP.md. Agents: AGENTS.md."
