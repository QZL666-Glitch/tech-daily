@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" main.py >> logs.txt 2>&1
