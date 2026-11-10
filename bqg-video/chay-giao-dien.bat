@echo off
REM Mo giao dien Xuong Video A.I Binh Quan (Windows)
cd /d "%~dp0"
if not exist config.toml copy config.example.toml config.toml
if not exist .venv (
  python -m venv .venv
  .venv\Scripts\pip install -r requirements.txt
)
.venv\Scripts\streamlit run webui\app.py
