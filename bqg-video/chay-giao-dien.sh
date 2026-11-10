#!/usr/bin/env bash
# Mở giao diện Xưởng Video A.I Bình Quân (Linux / macOS)
set -e
cd "$(dirname "$0")"
[ -f config.toml ] || cp config.example.toml config.toml
if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
exec .venv/bin/streamlit run webui/app.py
