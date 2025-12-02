import time
import random
import json
import logging
import asyncio
import platform
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

from crewai import Agent
from groq import Groq
from dotenv import load_dotenv
import os

# Try to import Playwright (optional for Railway deployment)
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("⚠️ Playwright not available - Daraz scraping will be disabled")

# Windows asyncio policy fix
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API keys from environment or Streamlit secrets
def get_api_key(key_name):
    """Get API key from environment or Streamlit secrets"""
    # Try environment variable first
    api_key = os.getenv(key_name)
    if api_key:
        return api_key
    
    # Try Streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key_name in st.secrets:
            return st.secrets[key_name]
    except:
        pass
    
    return None

# Lazy initialization of Groq client
groq_client = None

def get_groq_client():
    """Get or initialize Groq client"""
    global groq_client
    if groq_client is None:
        groq_api_key = get_api_key("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables or Streamlit secrets")
        groq_client = Groq(api_key=groq_api_key)
    return groq_client


def groq_api_call_with_retry(client: Groq, messages: List[Dict], model: str = "llama-3.1-8b-instant", max_retries: int = 5, base_delay: float = 1.0):
    """
    MANDATORY: Implement exponential backoff with jitter for Groq API rate limits
    """
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            error_str = str(e).lower()
            if "rate_limit" in error_str or "429" in error_str or "too many requests" in error_str:
                if attempt == max_retries - 1:
                    raise e
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Rate limit hit, retrying in {delay:.2f}s (attempt {attempt + 1})")
                time.sleep(delay)
                continue
            else:
                raise e
    
    return None


def handle_agent_errors(func):
    """Decorator for comprehensive error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Agent error in {func.__name__}: {e}")
            return {"error": str(e), "status": "failed"}
    return wrapper


class AgentA_DarazScraper(Agent):
    """
    Agent A: Daraz Scraping Agent
    Extracts product data from Daraz.pk using Playwright
    """
    
    def __init__(self):
        super().__init__(
            role="Daraz Product Data Extractor",
            goal="Extract comprehensive product information from Daraz.pk",
            backstory="""You are a specialized web scraping agent that extracts product data 
            from Daraz.pk, Pakistan's largest e-commerce platform. You use Playwright for 
            reliable data extraction and return structured JSON data.""",
            verbose=True,
            allow_delegation=False
        )
        # Store as class variables to avoid CrewAI field restrictions
        AgentA_DarazScraper._model = "llama-3.1-8b-instant"
    
    def scrape_daraz_product_sync(self, query: str, index: int = 0, headless: bool = False, 
                                 timeout: int = 60000, max_products: int = 1) -> dict:
        """
        Synchronous wrapper for scrape_daraz_product
        """
        try:
            if platform.system() == "Windows":
                # Ensure proper event loop for Windows
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        raise RuntimeError("Event loop is closed")
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                return loop.run_until_complete(
                    self.scrape_daraz_product(query, index, headless, timeout, max_products)
                )
            else:
                return asyncio.run(
                    self.scrape_daraz_product(query, index, headless, timeout, max_products)
                )
        except Exception as e:
            logger.error(f"❌ Sync wrapper error: {e}")
            return {"error": str(e), "status": "failed"}

    @handle_agent_errors
    async def scrape_daraz_product(self, query: str, index: int = 0, headless: bool = True, 
                                 timeout: int = 120000, max_products: int = 1) -> dict:
        """
        MANDATORY: Extract product data from Daraz.pk and return structured JSON
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("⚠️ Playwright not available - skipping Daraz scraping")
            return {"error": "Playwright not installed", "status": "skipped"}
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                }
            )
            page = await context.new_page()
            page.set_default_timeout(timeout)
            
            try:
                # Navigate to search page
                encoded_query = quote_plus(query)
                search_url = f"https://www.daraz.pk/catalog/?q={encoded_query}"
                
                logger.info(f"🔍 Agent A: Searching Daraz for: {query}")
                logger.info(f"📍 URL: {search_url}")
                
                # Try multiple times with different strategies
                loaded = False
                for attempt in range(3):
                    try:
                        if attempt == 0:
                            await page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
                        elif attempt == 1:
                            await page.goto(search_url, wait_until='load', timeout=70000)
                        else:
                            await page.goto(search_url, timeout=80000)
                        loaded = True
                        break
                    except Exception as e:
                        logger.warning(f"Attempt {attempt + 1} failed: {str(e)[:100]}")
                        if attempt < 2:
                            await page.wait_for_timeout(3000)
                            continue
                        else:
                            raise e
                
                if not loaded:
                    raise Exception("Failed to load Daraz after 3 attempts")
                
                # Find product links
                await page.wait_for_selector('a[href*="/products/"]', timeout=20000)
                
                selectors = [
                    'a[href*="/products/"][title]',
                    'a[title][href^="//www.daraz.pk/products/"]',
                    'a[href*="/products/"]'
                ]
                
                product_links = []
                for selector in selectors:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        href = await element.get_attribute('href')
                        title = await element.get_attribute('title') or await element.inner_text()
                        if href and title.strip():
                            product_links.append({'href': href, 'title': title.strip()})
                    
                    if product_links:
                        break
                
                if not product_links:
                    return {"error": "No products found", "status": "failed"}
                
                # Select product
                if index >= len(product_links):
                    index = 0
                
                selected_product = product_links[index]
                product_url = selected_product['href']
                
                if not product_url.startswith('http'):
                    product_url = f"https:{product_url}" if product_url.startswith('//') else f"https://www.daraz.pk{product_url}"
                
                logger.info(f"🎯 Agent A: Scraping: {selected_product['title'][:50]}...")
                
                # Navigate to product page
                await page.goto(product_url, wait_until='domcontentloaded')
                await page.wait_for_timeout(2000)  # Wait 2s for dynamic content
                
                # Extract product data with better filtering
                product_data = {
                    'url': product_url,
                    'title': selected_product['title']
                }
                
                # Extract clean title from page (sometimes better than link title)
                title_selectors = [
                    '[data-testid="pdp-product-title"]',
                    'h1[data-testid="pdp-product-title"]',
                    '.pdp-product-title',
                    'h1.pdp-mod-product-badge-title',
                    'h1'
                ]
                
                for selector in title_selectors:
                    try:
                        title_element = await page.query_selector(selector)
                        if title_element:
                            clean_title = await title_element.inner_text()
                            if clean_title and len(clean_title.strip()) > 10:
                                product_data['title'] = clean_title.strip()
                                break
                    except:
                        continue
                
                # Extract price - focus on main price only
                price_selectors = [
                    '[data-testid="pdp-price"] .currency',
                    '.pdp-price .currency',
                    '.pdp-product-price .currency',
                    '.price-current',
                    '[class*="price"]:not([class*="original"]):not([class*="discount"])'
                ]
                
                price_text = None
                for selector in price_selectors:
                    try:
                        price_element = await page.query_selector(selector)
                        if price_element:
                            price_text = await price_element.inner_text()
                            # Clean price text - remove extra info
                            if price_text and 'Rs' in price_text:
                                # Extract just the price part
                                import re
                                price_match = re.search(r'Rs[\s\.]*([0-9,]+)', price_text)
                                if price_match:
                                    price_text = f"Rs. {price_match.group(1)}"
                                break
                    except:
                        continue
                
                if price_text:
                    product_data['price_text'] = price_text.strip()
                    # Extract numeric price (PKR)
                    import re
                    price_numbers = re.findall(r'[\d,]+', price_text)
                    if price_numbers:
                        try:
                            price_numeric = int(price_numbers[0].replace(',', ''))
                            product_data['price_pkr'] = price_numeric
                        except:
                            pass
                
                # Extract seller - focus on main seller name only
                seller_selectors = [
                    '[data-testid="seller-name"] a',
                    '.seller-name a', 
                    '.pdp-seller-name a',
                    '[class*="seller"] a',
                    '.seller-link'
                ]
                
                seller_name = None
                for selector in seller_selectors:
                    try:
                        seller_element = await page.query_selector(selector)
                        if seller_element:
                            seller_text = await seller_element.inner_text()
                            # Clean seller name - avoid extra info
                            if seller_text and not any(word in seller_text.lower() for word in ['chat', 'store', 'rating', 'response', '%']):
                                seller_name = seller_text.strip()
                                break
                    except:
                        continue
                
                if seller_name:
                    product_data['seller'] = seller_name
                
                # Extract rating - focus on numerical rating only
                rating_selectors = [
                    '[data-testid="pdp-review-summary"] .score',
                    '.review-summary .score',
                    '.pdp-review .score',
                    '[class*="rating"] .score',
                    '.rating-average'
                ]
                
                for selector in rating_selectors:
                    try:
                        rating_element = await page.query_selector(selector)
                        if rating_element:
                            rating_text = await rating_element.inner_text()
                            # Extract only numerical rating
                            import re
                            rating_match = re.search(r'(\d\.?\d?)', rating_text)
                            if rating_match:
                                rating_value = float(rating_match.group(1))
                                if 0 <= rating_value <= 5:  # Valid rating range
                                    product_data['rating_average'] = rating_value
                                    break
                    except:
                        continue
                
                await browser.close()
                
                logger.info("✅ Agent A: Daraz scraping completed successfully")
                product_data['status'] = 'success'
                return product_data
                
            except Exception as e:
                await browser.close()
                logger.error(f"❌ Agent A: Scraping failed: {e}")
                return {"error": str(e), "status": "failed"}


class AgentB_SerperSearch(Agent):
    """
    Agent B: Serper.dev Search Agent
    Takes Daraz product name and searches Pakistani sites via Serper.dev
    """
    
    def __init__(self):
        # Don't check API key at init - will check when actually needed
        super().__init__(
            role="Pakistani E-commerce Site Search Agent",
            goal="Search Pakistani e-commerce sites using Serper.dev API for product comparison",
            backstory="""You are a specialized search agent that uses Serper.dev to find products 
            across Pakistani e-commerce platforms. You focus on PriceOye, OLX, Telemart, and other 
            local marketplaces to gather comprehensive price and availability data.""",
            verbose=True,
            allow_delegation=False
        )
    
    @handle_agent_errors
    def search_pakistani_sites(self, product_name: str, max_results: int = 10) -> dict:
        """
        MANDATORY: Search Pakistani e-commerce sites using Serper.dev
        Returns processed results directly (NO Agent C needed)
        """
        logger.info(f"🔍 Agent B: Searching Pakistani sites for: {product_name}")
        
        try:
            # Get API key when actually needed (lazy loading)
            api_key = get_api_key("SERPER_API_KEY")
            if not api_key:
                error_msg = "SERPER_API_KEY not found in environment variables or Streamlit secrets"
                logger.error(f"❌ Agent B: {error_msg}")
                return {
                    "status": "failed",
                    "error": error_msg,
                    "results": [],
                    "results_count": 0
                }
            
            logger.info(f"✅ Agent B: SERPER_API_KEY loaded successfully")
            
            base_url = "https://google.serper.dev"
            headers = {
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            }
            
            # Construct targeted search queries for Pakistani sites
            search_queries = [
                f"{product_name} site:priceoye.pk",
                f"{product_name} site:olx.com.pk",
                f"{product_name} site:telemart.pk",
                f"{product_name} site:shophive.pk",
                f"{product_name} site:daraz.pk",  # Include Daraz via search
                f"{product_name} price Pakistan buy online",
                f"buy {product_name} Pakistan online",
                f"{product_name} Pakistan price comparison"
            ]
            
            all_results = []
            
            for query in search_queries:
                try:
                    payload = {
                        "q": query,
                        "num": 10,  # Increased from 5 to 10 per query
                        "hl": "en",
                        "gl": "pk"  # Pakistan geo-location
                    }
                    
                    logger.info(f"📡 Agent B: Serper query: {query[:50]}...")
                    response = requests.post(
                        f"{base_url}/search",
                        headers=headers,
                        json=payload,
                        timeout=30
                    )
                    
                    logger.info(f"📡 Agent B: Serper response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        organic_results = data.get('organic', [])
                        
                        logger.info(f"📊 Agent B: Got {len(organic_results)} results for query")
                        
                        for result in organic_results:
                            # Process ALL results, not just Pakistani e-commerce
                            link = result.get('link', '')
                            
                            # Process if it's from Pakistani domains OR contains Pakistan-related keywords
                            is_pakistani = any(site in link.lower() for site in [
                                'daraz.pk', 'priceoye.pk', 'olx.com.pk', 'telemart.pk', 
                                'shophive.pk', 'homeshopping.pk', 'symbios.pk', 'goto.com.pk',
                                'yayvo.com', 'mega.pk'
                            ])
                            
                            # Also check if Pakistan is mentioned
                            snippet = result.get('snippet', '').lower()
                            title = result.get('title', '').lower()
                            has_pakistan = 'pakistan' in snippet or 'pakistan' in title or '.pk' in link
                            
                            if is_pakistani or has_pakistan:
                                processed_product = self._process_search_result(result)
                                if processed_product:
                                    all_results.append(processed_product)
                                    logger.info(f"✅ Agent B: Added result from {processed_product.get('platform', 'unknown')}")
                    else:
                        logger.error(f"❌ Agent B: Serper API returned status {response.status_code}: {response.text[:200]}")
                    
                    # Small delay between queries
                    time.sleep(0.5)
                
                except Exception as e:
                    logger.error(f"❌ Agent B: Query failed: {e}")
                    continue
        
            # Remove duplicates
            unique_results = []
            seen_urls = set()
            
            for result in all_results:
                url = result.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)
            
            logger.info(f"✅ Agent B: Found {len(unique_results)} unique results from Pakistani sites")
            logger.info(f"📊 Agent B: {sum(1 for r in unique_results if r.get('price_numeric'))} results have prices")
            
            return {
                "status": "success",
                "results": unique_results,
                "results_count": len(unique_results),
                "raw_results": all_results  # Keep for debugging
            }
            
        except Exception as e:
            logger.error(f"❌ Agent B: Critical error in search_pakistani_sites: {e}")
            logger.exception("Full traceback:")
            return {
                "status": "failed",
                "error": str(e),
                "results": [],
                "results_count": 0
            }
    
    def _process_search_result(self, result: dict) -> dict:
        """
        DIRECT PROCESSING: Process individual search result without Agent C
        """
        try:
            title = result.get('title', 'Unknown Product')
            link = result.get('link', '')
            snippet = result.get('snippet', '')
            
            # Extract price from title or snippet using regex - MORE PATTERNS
            import re
            price_patterns = [
                r'Rs\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # Rs. 50,000 or Rs. 50,000.00
                r'PKR\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', # PKR 50,000
                r'(\d+(?:,\d{3})*)\s*(?:Rs|PKR)',         # 50,000 Rs
                r'Price:\s*Rs\.?\s*(\d+(?:,\d{3})*)',     # Price: Rs. 50,000
                r'₨\s*(\d+(?:,\d{3})*)',                  # ₨ 50,000
            ]
            
            price_numeric = None
            price_text = "Price not available"
            
            text_to_search = f"{title} {snippet}"
            for pattern in price_patterns:
                match = re.search(pattern, text_to_search, re.IGNORECASE)
                if match:
                    try:
                        price_str = match.group(1).replace(',', '').replace('.00', '')
                        price_numeric = int(float(price_str))
                        
                        # Smart price validation based on product category
                        if self._is_valid_price_for_product(title, price_numeric):
                            price_text = f"Rs. {price_numeric:,}"
                            break
                        else:
                            price_numeric = None
                    except:
                        continue
            
            # Determine platform
            platform = self._extract_domain(link)
            
            return {
                "title": title,
                "price_text": price_text,
                "price_numeric": price_numeric,
                "currency": "PKR",
                "platform": platform,
                "url": link,
                "availability": "unknown",
                "seller": "unknown",
                "specifications": [],
                "confidence": 0.8 if price_numeric else 0.5
            }
            
        except Exception as e:
            logger.error(f"Error processing result: {e}")
            return None
    
    def _is_valid_price_for_product(self, title: str, price: int) -> bool:
        """
        Validate price based on product category to filter out unrealistic prices
        """
        title_lower = title.lower()
        
        # Electronics categories with realistic price ranges
        price_ranges = {
            # Smartphones
            'iphone': (50000, 500000),
            'samsung': (15000, 400000),
            'xiaomi': (15000, 150000),
            'redmi': (15000, 100000),
            'oppo': (15000, 150000),
            'vivo': (15000, 150000),
            'realme': (15000, 100000),
            'oneplus': (40000, 200000),
            'huawei': (20000, 200000),
            'phone': (10000, 500000),
            'mobile': (10000, 500000),
            
            # Laptops
            'laptop': (30000, 1000000),
            'macbook': (150000, 1000000),
            'dell': (30000, 500000),
            'hp': (30000, 500000),
            'lenovo': (30000, 500000),
            'asus': (30000, 500000),
            
            # Tablets
            'ipad': (50000, 500000),
            'tablet': (15000, 300000),
            
            # Watches
            'watch': (2000, 500000),
            'apple watch': (50000, 300000),
            
            # Audio
            'airpods': (5000, 100000),
            'earbuds': (1000, 100000),
            'headphones': (1000, 100000),
            'speaker': (2000, 200000),
            
            # Gaming
            'playstation': (50000, 300000),
            'ps5': (100000, 300000),
            'ps4': (30000, 150000),
            'xbox': (50000, 300000),
            
            # Accessories
            'charger': (500, 20000),
            'cable': (200, 10000),
            'case': (300, 20000),
            'cover': (300, 20000),
            'protector': (200, 5000),
        }
        
        # Check which category matches
        for keyword, (min_price, max_price) in price_ranges.items():
            if keyword in title_lower:
                if min_price <= price <= max_price:
                    return True
                else:
                    logger.info(f"🚫 Rejected price {price} for '{title}' (expected {min_price}-{max_price})")
                    return False
        
        # Default range for unknown products
        if 1000 <= price <= 1000000:
            return True
        
        logger.info(f"🚫 Rejected unrealistic price {price} for '{title}'")
        return False

    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.lower()
            domain = domain.replace('www.', '')
            
            # Map to clean names
            domain_map = {
                'priceoye.pk': 'PriceOye',
                'olx.com.pk': 'OLX Pakistan', 
                'telemart.pk': 'Telemart',
                'shophive.pk': 'Shophive'
            }
            return domain_map.get(domain, domain)
        except:
            return "unknown"


class AgentD_ReportGenerator(Agent):
    """
    Agent D: Report Generation Agent
    Takes Daraz data + processed search results and generates final comparison report
    """
    
    def __init__(self):
        super().__init__(
            role="E-commerce Comparison Report Generator",
            goal="Generate comprehensive price comparison reports using AI analysis",
            backstory="""You are an expert business analyst specializing in Pakistani e-commerce. 
            You create detailed comparison reports that help consumers make informed purchasing decisions 
            by analyzing price trends, vendor reliability, and market conditions.""",
            verbose=True,
            allow_delegation=False
        )
        # Store as class variables to avoid CrewAI field restrictions
        AgentD_ReportGenerator._model = "llama-3.1-8b-instant"
    
    @handle_agent_errors
    def generate_final_report(self, daraz_data: dict, serper_data: dict, query: str) -> dict:
        """
        MANDATORY: Generate comprehensive comparison report
        Takes direct search results from Agent B (no Agent C processing needed)
        """
        logger.info(f"📊 Agent D: Generating comprehensive report for: {query}")
        
        # Prepare data for report
        all_products = []
        
        # Add Daraz product
        if daraz_data.get('status') == 'success':
            daraz_product = {
                'title': daraz_data.get('title', ''),
                'price_text': daraz_data.get('price_text', ''),
                'price_numeric': daraz_data.get('price_pkr'),
                'platform': 'Daraz.pk',
                'url': daraz_data.get('url', ''),
                'seller': daraz_data.get('seller', 'Unknown'),
                'rating': daraz_data.get('rating_average'),
                'confidence': 1.0  # High confidence for direct scraping
            }
            all_products.append(daraz_product)
        
        # Add search results from Agent B
        if serper_data.get('status') == 'success':
            search_results = serper_data.get('results', [])
            all_products.extend(search_results)
        
        if not all_products:
            return {
                "error": "No product data available for report generation",
                "status": "failed"
            }
        
        # Generate report using Groq LLM
        products_summary = "\n".join([
            f"Platform: {p.get('platform', 'Unknown')}\n"
            f"Title: {p.get('title', 'Unknown')}\n"
            f"Price: {p.get('price_text', 'N/A')} (Numeric: {p.get('price_numeric', 'N/A')})\n"
            f"URL: {p.get('url', 'N/A')}\n"
            f"Confidence: {p.get('confidence', 0)}\n"
            "---"
            for p in all_products
        ])
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert Pakistani e-commerce analyst. Create a comprehensive comparison report that helps consumers make informed purchasing decisions.

Your report should include:
1. Executive Summary
2. Price Comparison (lowest to highest)
3. Platform Analysis (reliability, reputation)
4. Best Value Recommendations
5. Market Insights specific to Pakistan
6. Buying Recommendations

Focus on Pakistani market conditions, local seller reliability, and consumer preferences.
Use Pakistani Rupees (PKR) for all price discussions.
Consider factors like:
- PTA approval (for electronics)
- Local warranty vs international warranty
- Shipping costs and delivery time in Pakistan
- Payment methods available in Pakistan

Return structured analysis as plain text (not JSON) formatted for markdown."""
            },
            {
                "role": "user",
                "content": f"""Generate a comprehensive comparison report for: "{query}"

Product Data:
{products_summary}

Generate detailed analysis focusing on Pakistani market conditions, local sellers, and consumer preferences."""
            }
        ]
        
        try:
            response = groq_api_call_with_retry(
                get_groq_client(),
                messages,
                model=AgentD_ReportGenerator._model
            )
            
            # Try to extract structured data from response
            try:
                # Parse the response to extract key insights
                report_data = {
                    "full_report": response,
                    "best_deals": self._extract_best_deals(all_products),
                    "market_insights": self._extract_market_insights(all_products),
                    "buying_recommendations": response.split("Buying Recommendations")[-1][:500] if "Buying Recommendations" in response else "See full report"
                }
                
                # Save report to file
                report_file = self._save_report_to_file(query, response, all_products)
                
                logger.info(f"✅ Agent D: Report generated successfully")
                return {
                    "status": "success",
                    "report": report_data,
                    "report_file": report_file,
                    "products_analyzed": len(all_products)
                }
                
            except Exception as parse_error:
                logger.error(f"❌ Agent D: JSON parsing failed: {parse_error}")
                
                # Save simple report even if parsing fails
                report_file = self._save_report_to_file(query, response, all_products)
                
                return {
                    "status": "partial_success",
                    "report": {
                        "full_report": response,
                        "best_deals": self._extract_best_deals(all_products),
                        "market_insights": {"total_products": len(all_products)},
                        "parsing_error": str(parse_error)
                    },
                    "report_file": report_file,
                    "products_analyzed": len(all_products)
                }
                
        except Exception as e:
            logger.error(f"❌ Agent D: Report generation failed: {e}")
            
            # Fallback: create basic report without LLM
            basic_report = self._create_fallback_report(query, all_products)
            report_file = self._save_report_to_file(query, basic_report, all_products)
            
            return {
                "status": "failed_with_fallback",
                "report": {
                    "full_report": basic_report,
                    "best_deals": self._extract_best_deals(all_products),
                    "market_insights": {"total_products": len(all_products)},
                    "error": str(e)
                },
                "report_file": report_file,
                "products_analyzed": len(all_products)
            }
    
    def _extract_best_deals(self, products: List[dict]) -> dict:
        """Extract best deals from product list"""
        valid_prices = [p for p in products if p.get('price_numeric')]
        if not valid_prices:
            return {}
        
        cheapest = min(valid_prices, key=lambda x: x['price_numeric'])
        most_expensive = max(valid_prices, key=lambda x: x['price_numeric'])
        
        return {
            "cheapest": {
                "platform": cheapest.get('platform'),
                "price": cheapest.get('price_numeric'),
                "title": cheapest.get('title', '')[:50]
            },
            "most_expensive": {
                "platform": most_expensive.get('platform'),
                "price": most_expensive.get('price_numeric'),
                "title": most_expensive.get('title', '')[:50]
            },
            "price_difference": most_expensive['price_numeric'] - cheapest['price_numeric']
        }
    
    def _extract_market_insights(self, products: List[dict]) -> dict:
        """Extract market insights from products"""
        total_products = len(products)
        platforms = set(p.get('platform') for p in products if p.get('platform'))
        
        prices = [p['price_numeric'] for p in products if p.get('price_numeric')]
        
        insights = {
            "total_products": total_products,
            "platforms_found": list(platforms),
            "platform_count": len(platforms)
        }
        
        if prices:
            insights["price_range"] = {
                "min_price": min(prices),
                "max_price": max(prices),
                "average_price": sum(prices) / len(prices)
            }
        
        return insights
    
    def _create_fallback_report(self, query: str, products: List[dict]) -> str:
        """Create basic report without LLM"""
        report = f"# Price Comparison Report: {query}\n\n"
        report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += f"## Summary\n"
        report += f"Total products found: {len(products)}\n\n"
        
        report += "## Product Listings\n\n"
        for i, product in enumerate(products, 1):
            report += f"### {i}. {product.get('platform', 'Unknown')}\n"
            report += f"**Title:** {product.get('title', 'N/A')}\n"
            report += f"**Price:** {product.get('price_text', 'N/A')}\n"
            report += f"**URL:** {product.get('url', 'N/A')}\n\n"
        
        return report
    
    def _save_report_to_file(self, query: str, content: str, products: List[dict]) -> str:
        """Save report to markdown file"""
        try:
            # Create reports directory
            reports_dir = Path("data/reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            query_safe = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
            query_safe = query_safe.replace(' ', '-')[:30]
            
            filename = f"{query_safe}-{timestamp}-comparison.md"
            filepath = reports_dir / filename
            
            # Create full report with metadata
            full_report = f"# Pakistani E-commerce Price Comparison\n\n"
            full_report += f"**Query:** {query}\n"
            full_report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            full_report += f"**Products Analyzed:** {len(products)}\n"
            full_report += f"**Analysis Method:** CrewAI Multi-Agent System\n\n"
            full_report += "---\n\n"
            full_report += content
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_report)
            
            logger.info(f"📄 Report saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return None


# Agent factory function
def get_new_agents() -> Dict[str, Agent]:
    """Get all agents for the new architecture (NO Agent C)"""
    return {
        'agent_a_daraz': AgentA_DarazScraper(),
        'agent_b_serper': AgentB_SerperSearch(), 
        'agent_d_report': AgentD_ReportGenerator()
    }
