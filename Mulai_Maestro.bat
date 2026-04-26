@echo off
title Maestro Trading Intelligence v3.0
color 0B
echo ============================================================
echo   MAESTRO TRADING INTELLIGENCE v3.0
echo ============================================================
pip install streamlit yfinance pandas plotly scipy numpy requests beautifulsoup4 lxml >nul 2>&1
echo Membuka aplikasi di browser...
streamlit run Maestro_App.py
pause
