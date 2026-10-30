@echo off
chcp 65001 >nul
python -m pip install -r requirements.txt
python scripts\import_data.py
python src\main.py
pause
