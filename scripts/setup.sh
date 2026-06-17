#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

if command -v apt-get >/dev/null 2>&1; then
  echo "Installing system packages needed by OpenCV/FFmpeg..."
  sudo apt-get update
  sudo apt-get install -y libgl1 libglib2.0-0 ffmpeg python3-pip python3-venv git
else
  echo "apt-get not found; install OpenCV/FFmpeg system packages manually."
fi

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Setup complete. Activate with: source .venv/bin/activate"
