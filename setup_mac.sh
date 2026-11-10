#!/bin/bash
set -euo pipefail

# Run from the repository root. Uses an isolated Python virtual environment.
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed. Install Python 3.11+ from https://www.python.org/downloads/macos/ and retry."
  exit 1
fi
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo "Environment ready. Activate it later with: source .venv/bin/activate"
