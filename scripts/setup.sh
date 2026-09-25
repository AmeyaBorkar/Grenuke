#!/usr/bin/env bash
# One-time setup for a clone of the Grenuke repo (macOS / Linux / Git Bash).
# Usage (from anywhere):
#   bash scripts/setup.sh          # git config + hooks only
#   bash scripts/setup.sh --venv   # also create .venv and install the package
set -euo pipefail
cd "$(dirname "$0")/.."

# Enforcement hooks (commit-msg / pre-commit / pre-push) live in .githooks
git config core.hooksPath .githooks
git config pull.rebase true
git config fetch.prune true
git config rebase.autoStash true
chmod +x .githooks/* 2>/dev/null || true

if [ -z "$(git config user.name || true)" ] || [ -z "$(git config user.email || true)" ]; then
  echo "WARNING: set your git identity: git config --global user.name 'Your Name'; git config --global user.email 'you@example.com'" >&2
fi

if [ "${1:-}" = "--venv" ]; then
  PY="${PYTHON:-python3}"
  command -v "$PY" >/dev/null 2>&1 || PY=python
  [ -d .venv ] || "$PY" -m venv .venv
  if [ -x .venv/bin/python ]; then VPY=.venv/bin/python; else VPY=.venv/Scripts/python; fi
  "$VPY" -m pip install --upgrade pip
  "$VPY" -m pip install -e "code/business_entity_resolution[dev]"
  echo "Venv ready. Activate with: source .venv/bin/activate"
  echo "Full pinned env: pip install -r code/business_entity_resolution/requirements.txt"
fi

echo "core.hooksPath = $(git config core.hooksPath)"
echo "Put the Unstop dataset in student_resource/dataset/{train,test}/ (git-ignored; never commit it)."
echo "Next: read CONTRIBUTING.md, docs/TEAM.md, docs/ROADMAP.md. Agents: AGENTS.md."
