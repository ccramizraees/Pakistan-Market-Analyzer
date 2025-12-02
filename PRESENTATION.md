# 🛍️ Pakistani E-commerce Marketplace Analyzer
## AI-Powered Price Comparison Platform

---

## 📋 Project Overview

**Problem Statement:**
- Pakistani consumers struggle to find the best prices across multiple e-commerce platforms
- Manual price comparison is time-consuming and inefficient
- No centralized tool for comparing prices from Daraz, PriceOye, OLX, Telemart, etc.

**Solution:**
An intelligent multi-agent system that automatically scrapes, searches, and compares prices across all major Pakistani e-commerce platforms in real-time.

---

## 🎯 Key Features

### 1. **Multi-Platform Search**
- Daraz.pk (Direct web scraping)
- PriceOye, OLX, Telemart, Shophive (API-based search)
- Real-time price extraction and comparison

### 2. **AI-Powered Analysis**
- Uses Groq LLM for intelligent market insights
- Generates comprehensive comparison reports
- Provides buying recommendations

### 3. **User-Friendly Interface**
- Modern Streamlit web application
- Interactive charts and visualizations
- Mobile-responsive design

### 4. **Data Persistence**
- SQLite database for historical tracking
- Markdown reports for detailed analysis
- Recent search history

---

## 🏗️ System Architecture

### **Multi-Agent CrewAI System**

```
┌─────────────────────────────────────────────┐
│           User Search Query                  │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────▼──────────┐
        │   Streamlit UI      │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────────────┐
        │   CrewAI Orchestrator       │
        └──────────┬──────────────────┘
                   │
        ┌──────────┴──────────────────────────┐
        │                                      │
   ┌────▼─────┐  ┌────────────┐  ┌───────────▼────┐
   │ Agent A  │  │  Agent B   │  │   Agent D      │
   │  Daraz   │  │  Serper    │  │   Report       │
   │ Scraper  │  │  Search    │  │  Generator     │
   └────┬─────┘  └─────┬──────┘  └───────┬────────┘
        │              │                  │
        └──────────────┴──────────────────┘
                       │
              ┌────────▼─────────┐
              │  Database & File  │
              │     Storage       │
              └───────────────────┘
```

### **Agent Responsibilities:**

**Agent A - Daraz Scraper**
- Uses Playwright for web automation
- Extracts product details, prices, ratings, sellers
- Handles dynamic content and anti-bot measures

**Agent B - Serper Search**
- Searches Pakistani marketplaces via Serper.dev API
- Processes and extracts price information
- Filters and deduplicates results

**Agent D - Report Generator**
- Analyzes all collected data
- Generates comprehensive markdown reports
- Provides market insights and recommendations

---

## 💻 Technology Stack

### **Backend**
- **Python 3.13** - Core programming language
- **CrewAI** - Multi-agent orchestration framework
- **Playwright** - Web scraping and automation
- **Groq API** - LLM for AI analysis

### **Frontend**
- **Streamlit** - Web application framework
- **Plotly** - Interactive data visualization
- **Pandas** - Data manipulation

### **APIs**
- **Serper.dev** - Google search API for marketplace discovery
- **Groq** - AI-powered analysis and report generation

### **Data Storage**
- **SQLite** - Local database for queries and results
- **Markdown Files** - Human-readable reports

---

## 📊 Live Demo - User Journey

### **Step 1: Search**
User enters product name (e.g., "iPhone 15 Pro Max")

### **Step 2: Processing**
- System scrapes Daraz.pk for official listings
- Searches other Pakistani marketplaces
- Processes and validates price data

### **Step 3: Analysis**
- AI analyzes all collected data
- Identifies best deals and price trends
- Generates market insights

### **Step 4: Results**
- Interactive price comparison table
- Visual charts showing price differences
- Comprehensive markdown report
- Direct links to all products

---

## 📈 Sample Output

### **Price Comparison (Example)**

| Rank | Platform | Price (PKR) | Difference |
|------|----------|-------------|------------|
| 🥇 | OLX Pakistan | Rs. 285,000 | **Best Price!** |
| 🥈 | PriceOye | Rs. 289,999 | +Rs. 4,999 |
| 🥉 | Telemart | Rs. 295,000 | +Rs. 10,000 |
| 4. | Daraz.pk | Rs. 299,999 | +Rs. 14,999 |

### **Key Insights**
- **Max Savings:** Rs. 14,999 (5.0%)
- **Average Price:** Rs. 292,500
- **Platforms Found:** 4
- **Best Deal:** OLX Pakistan

---

## 🎯 Project Highlights

### **Innovation**
- First comprehensive multi-platform price tracker for Pakistan
- AI-powered analysis specific to Pakistani market conditions
- Considers local factors (PTA approval, warranty, delivery)

### **Technical Excellence**
- Robust error handling and retry mechanisms
- Asynchronous processing for faster results
- Scalable multi-agent architecture

### **User Experience**
- Clean, modern interface
- Real-time progress indicators
- Downloadable reports

### **Business Value**
- Saves consumers time and money
- Promotes market transparency
- Helps identify pricing trends

---

## 🔄 System Flow

1. **User Input** → Search query entered
2. **Agent A** → Scrapes Daraz.pk for detailed product info
3. **Agent B** → Searches other Pakistani marketplaces
4. **Data Processing** → Validates and deduplicates results
5. **Agent D** → Generates AI-powered analysis report
6. **Storage** → Saves to database and file system
7. **Display** → Shows results with charts and insights

---

## 📝 Code Quality Features

### **Error Handling**
- Comprehensive try-catch blocks
- Graceful degradation (continues even if one source fails)
- Detailed logging for debugging

### **Performance Optimization**
- Parallel API calls where possible
- Rate limiting and retry logic
- Efficient data structures

### **Maintainability**
- Clean separation of concerns
- Modular agent architecture
- Well-documented code

---

## 🚀 Future Enhancements

### **Phase 1 (Current)**
- ✅ Multi-platform price comparison
- ✅ AI-powered analysis
- ✅ Report generation

### **Phase 2 (Planned)**
- 🔄 Price tracking and alerts
- 🔄 Historical price charts
- 🔄 User accounts and saved searches

### **Phase 3 (Future)**
- 📱 Mobile application
- 🔔 Push notifications for price drops
- 🤖 Chatbot for product recommendations
- 📊 Advanced analytics dashboard

---

## 💡 Key Takeaways

### **For Consumers:**
- Save money by finding best prices
- Make informed purchasing decisions
- Access comprehensive market data

### **For Developers:**
- Demonstrates multi-agent AI systems
- Real-world web scraping challenges
- Full-stack application development

### **For Business:**
- Market research capabilities
- Competitive pricing intelligence
- Consumer behavior insights

---

## 🛠️ Setup & Installation

```bash
# 1. Clone repository
git clone <repo-url>

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
playwright install chromium

# 5. Configure API keys
# Create .env file with:
GROQ_API_KEY=your_groq_key
SERPER_API_KEY=your_serper_key

# 6. Run application
streamlit run streamlit_app.py
```

---

## 📞 Q&A

### **Common Questions:**

**Q: How long does a search take?**
A: Typically 15-30 seconds depending on network and sources

**Q: Is this legal?**
A: Yes - scrapes public data for personal use

**Q: Can it track price history?**
A: Yes - all searches saved to database with timestamps

**Q: What if a website blocks scraping?**
A: System continues with other sources and provides partial results

**Q: Is it accurate?**
A: High accuracy - directly extracts prices from source websites

---

## 🎓 Learning Outcomes

### **Technical Skills Demonstrated:**
- Multi-agent AI system design
- Web scraping with anti-detection
- API integration (Groq, Serper)
- Full-stack web development
- Database design and management
- Error handling and logging
- User interface design

### **Soft Skills:**
- Problem-solving
- System architecture
- User-centric design
- Documentation

---

## 📊 Project Statistics

- **Lines of Code:** ~2,500+
- **Python Files:** 10+
- **Agents:** 3 (Specialized AI agents)
- **Platforms Covered:** 5+ Pakistani marketplaces
- **Average Search Time:** 20 seconds
- **Success Rate:** 85%+ (with fallbacks)

---

## 🏆 Conclusion

### **Project Success:**
✅ Solves real-world problem for Pakistani consumers
✅ Demonstrates advanced AI and automation techniques
✅ Production-ready with error handling and logging
✅ Scalable architecture for future enhancements
✅ User-friendly interface with modern design

### **Impact:**
- Empowers consumers with price transparency
- Saves time and money
- Promotes competitive pricing in Pakistani e-commerce

---

## 🙏 Thank You!

**Questions?**

**Live Demo Available**
- Local URL: http://localhost:8501

**Repository:** [Your GitHub Link]

**Contact:** [Your Email]

---

*Pakistani E-commerce Marketplace Analyzer*
*Powered by CrewAI, Groq, and Serper.dev*
