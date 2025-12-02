#!/bin/bash

# Install Playwright dependencies
playwright install-deps chromium

# Install Playwright browser
playwright install chromium

# Start Streamlit
streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
