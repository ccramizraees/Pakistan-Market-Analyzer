# Pakistani E-commerce Marketplace Analyzer

This project is a price comparison and intelligence tool for Pakistani e-commerce platforms. It scrapes product data from Daraz.pk and searches other local marketplaces (PriceOye, OLX, Telemart, Shophive, etc.) using Serper.dev. The system analyzes prices, generates comparison reports, and provides market insights using Groq LLM.

## 🌟 Features
- 🔍 Multi-platform price comparison across Pakistani marketplaces
- 🤖 AI-powered market analysis using Groq LLM
- 📊 Interactive data visualizations with Plotly
- 📄 Comprehensive markdown reports
- 💾 SQLite database for historical tracking
- 🎨 Modern, responsive Streamlit UI

## 🛠️ Technology Stack
- **Backend:** Python, CrewAI, Playwright, Groq
- **Frontend:** Streamlit, Plotly, Pandas
- **APIs:** Serper.dev, Groq
- **Database:** SQLite

## 📋 How It Works
1. Scrapes product details from Daraz.pk using Playwright
2. Searches other platforms via Serper.dev API
3. Analyzes and compares prices using Groq LLM
4. Generates markdown reports and saves results to SQLite database
5. Displays results in an interactive Streamlit interface

## 🚀 Setup & Usage

### Local Development
1. Clone the repository
   ```bash
   git clone https://github.com/ccramizraees/Pakistan-Market-Analyzer.git
   cd Pakistan-Market-Analyzer
   ```

2. Create a virtual environment
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

4. Create a `.env` file with your API keys
   ```env
   GROQ_API_KEY=your_groq_key_here
   SERPER_API_KEY=your_serper_key_here
   ```

5. Run the application
   ```bash
   streamlit run streamlit_app.py
   ```
   Or use the CLI:
   ```bash
   python main.py "product name"
   ```

### ☁️ Streamlit Cloud Deployment

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io/)
   - Click "New app"
   - Select your repository: `ccramizraees/Pakistan-Market-Analyzer`
   - Branch: `main`
   - Main file: `streamlit_app.py`

3. **Add API Keys as Secrets**
   - In your app dashboard, go to **Settings → Secrets**
   - Add your API keys in TOML format:
   ```toml
   GROQ_API_KEY = "your_groq_key_here"
   SERPER_API_KEY = "your_serper_key_here"
   ```

4. **Deploy!** The app will automatically install dependencies and start.

## 🔑 Getting API Keys

### Groq API Key
1. Go to [console.groq.com](https://console.groq.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key

### Serper API Key
1. Go to [serper.dev](https://serper.dev/)
2. Sign up for an account
3. Get your API key from the dashboard

## 📊 Usage Example

1. Enter a product name (e.g., "iPhone 15 Pro Max")
2. The system will:
   - Search Daraz.pk for detailed product info
   - Search other Pakistani marketplaces (PriceOye, OLX, Telemart)
   - Compare prices across all platforms
   - Generate AI-powered insights and recommendations
3. View results with:
   - Interactive price comparison table
   - Visual charts showing price differences
   - Comprehensive markdown report
   - Direct links to all products

## 🎯 Project Structure

```
Pakistan-Market-Analyzer/
├── streamlit_app.py          # Main Streamlit application
├── main.py                   # CLI interface
├── requirements.txt          # Python dependencies
├── packages.txt             # System packages for Streamlit Cloud
├── .streamlit/
│   └── config.toml          # Streamlit configuration
├── src/
│   ├── crew/
│   │   ├── agents.py        # CrewAI agent definitions
│   │   ├── crew.py          # Crew orchestration
│   │   └── tasks.py         # Task definitions
│   └── database/
│       └── models.py        # Database models
├── data/
│   ├── reports/             # Generated markdown reports
│   └── recent_searches.json # Search history
└── PRESENTATION.md          # Project presentation
```

## 🤖 Multi-Agent System

The project uses CrewAI with three specialized agents:

1. **Agent A (Daraz Scraper):** Extracts product data from Daraz.pk using Playwright
2. **Agent B (Serper Search):** Searches Pakistani marketplaces via Serper.dev API
3. **Agent D (Report Generator):** Generates comprehensive analysis using Groq LLM

## 📝 License
MIT License

## 👨‍💻 Author
Ramiz Raees

## 🙏 Acknowledgments
- CrewAI for multi-agent framework
- Groq for LLM API
- Serper.dev for search API
- Streamlit for the web framework
