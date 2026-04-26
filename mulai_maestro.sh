#!/bin/bash
echo "Maestro Trading System v3.0"
echo "Menginstall dependensi..."
pip install streamlit yfinance pandas plotly scipy numpy requests beautifulsoup4 lxml -q
echo "Membuka aplikasi..."
streamlit run Maestro_App.py
