@echo off
cd /d "%~dp0"
echo Starting crj AI Digital Twin...
echo.
python -m streamlit run app/main.py --server.port 8501
pause
