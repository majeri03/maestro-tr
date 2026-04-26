@echo off
title Maestro Trading Terminal
color 0B
echo ============================================================
echo   MAESTRO TRADING SYSTEM v3.0
echo   Mempersiapkan mesin...
echo ============================================================
pip install streamlit yfinance pandas plotly scipy numpy requests beautifulsoup4 lxml >nul 2>&1
echo Mesin siap! Membuka di browser...
streamlit run Maestro_App.py
pause
