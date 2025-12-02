"""Health check script to test all imports before starting Streamlit"""
import sys

print("🔍 Testing imports...")

try:
    print("✓ Testing standard library...")
    import json
    import logging
    import os
    print("  ✓ Standard library OK")
except Exception as e:
    print(f"  ✗ Standard library failed: {e}")
    sys.exit(1)

try:
    print("✓ Testing Streamlit...")
    import streamlit
    print(f"  ✓ Streamlit {streamlit.__version__} OK")
except Exception as e:
    print(f"  ✗ Streamlit failed: {e}")
    sys.exit(1)

try:
    print("✓ Testing dotenv...")
    from dotenv import load_dotenv
    print("  ✓ dotenv OK")
except Exception as e:
    print(f"  ✗ dotenv failed: {e}")
    sys.exit(1)

try:
    print("✓ Testing requests...")
    import requests
    print("  ✓ requests OK")
except Exception as e:
    print(f"  ✗ requests failed: {e}")
    sys.exit(1)

try:
    print("✓ Testing Groq...")
    from groq import Groq
    print("  ✓ Groq OK")
except Exception as e:
    print(f"  ✗ Groq failed: {e}")
    sys.exit(1)

try:
    print("✓ Testing CrewAI...")
    from crewai import Agent, Crew
    print("  ✓ CrewAI OK")
except Exception as e:
    print(f"  ✗ CrewAI failed: {e}")
    sys.exit(1)

try:
    print("✓ Testing pandas...")
    import pandas
    print("  ✓ pandas OK")
except Exception as e:
    print(f"  ✗ pandas failed: {e}")
    sys.exit(1)

try:
    print("✓ Testing plotly...")
    import plotly
    print("  ✓ plotly OK")
except Exception as e:
    print(f"  ✗ plotly failed: {e}")
    sys.exit(1)

try:
    print("✓ Testing Playwright (optional)...")
    from playwright.async_api import async_playwright
    print("  ✓ Playwright OK (available)")
except ImportError:
    print("  ⚠ Playwright not available (expected for Railway)")

print("\n✅ All critical imports successful!")
print("🚀 App should start correctly\n")
