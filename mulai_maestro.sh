#!/bin/bash
echo "Maestro Trading Intelligence v3.0"
pip install streamlit yfinance pandas plotly scipy numpy requests beautifulsoup4 lxml -q
streamlit run Maestro_App.py
