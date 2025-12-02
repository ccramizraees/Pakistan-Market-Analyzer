# 🚀 Deploy Pakistani Price Tracker to Railway

Railway is the **BEST** platform for this app because:
- ✅ Supports Playwright with full browser automation
- ✅ Better error handling and logging
- ✅ More reliable than Streamlit Cloud
- ✅ Proper environment variable management
- ✅ Free tier with good limits

## 📋 Prerequisites

1. GitHub account with your repository pushed
2. Railway account (sign up at https://railway.app/)
3. Your API keys ready:
   - `GROQ_API_KEY`
   - `SERPER_API_KEY`
   - `OPENAI_API_KEY` (dummy: "sk-dummy-key-not-used")

## 🎯 Deployment Steps

### Step 1: Create Railway Project

1. Go to https://railway.app/
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select your repository: `ccramizraees/Pakistan-Market-Analyzer`

### Step 2: Configure Environment Variables

In Railway dashboard:

1. Click on your project
2. Go to **"Variables"** tab
3. Add these variables:

```
GROQ_API_KEY=your_actual_groq_api_key_here
SERPER_API_KEY=your_actual_serper_api_key_here
OPENAI_API_KEY=sk-dummy-key-not-used
PORT=8501
```

### Step 3: Configure Build Settings

Railway should auto-detect the configuration, but verify:

1. **Build Command**: 
   ```bash
   pip install -r requirements.txt && playwright install chromium && playwright install-deps
   ```

2. **Start Command**:
   ```bash
   streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
   ```

3. **Root Directory**: `/` (leave default)

### Step 4: Deploy!

1. Railway will automatically deploy after configuration
2. Wait 3-5 minutes for build and deployment
3. Click on **"Generate Domain"** to get your public URL
4. Visit your app: `https://your-app-name.up.railway.app`

## 🔧 Troubleshooting

### If Playwright fails:

Add this to Railway environment variables:
```
PLAYWRIGHT_BROWSERS_PATH=/app/.cache/ms-playwright
```

### If port binding fails:

Ensure these variables are set:
```
PORT=8501
STREAMLIT_SERVER_PORT=$PORT
```

### If build takes too long:

Railway free tier has build timeouts. The app should build in 2-3 minutes.

## 📊 Monitoring

Railway provides:

- **Logs**: Real-time application logs
- **Metrics**: CPU, Memory, Network usage
- **Deployments**: History of all deployments
- **Variables**: Easy environment variable management

## 💰 Costs

- **Free Tier**: $5/month credit (enough for development)
- **Hobby Plan**: $5/month for more resources
- **Pro Plan**: $20/month for production apps

## 🎉 Post-Deployment

Once deployed:

1. Test search functionality
2. Verify Daraz scraping works (Playwright)
3. Check price comparisons
4. Download reports

Your app will have:
- ✅ Full Playwright support (Daraz scraping works!)
- ✅ Smart price filtering
- ✅ All 3 agents working (A, B, D)
- ✅ Proper error handling
- ✅ Persistent storage for reports

## 🔗 Useful Links

- Railway Dashboard: https://railway.app/dashboard
- Railway Docs: https://docs.railway.app/
- Your GitHub Repo: https://github.com/ccramizraees/Pakistan-Market-Analyzer

---

**Note**: Railway is 10x better than Streamlit Cloud for this app because Playwright actually works there!
