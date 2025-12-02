#!/bin/bash
set -e

echo "Installing Playwright dependencies..."
playwright install-deps chromium || echo "Warning: Failed to install playwright deps"

echo "Installing Playwright browser..."
playwright install chromium || echo "Warning: Failed to install chromium"

echo "Starting Streamlit..."
exec streamlit run streamlit_app.py --server.port ${PORT:-8501} --server.address 0.0.0.0 --server.headless true
