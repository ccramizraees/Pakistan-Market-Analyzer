import time
import random
import json
import logging
import requests
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

from crewai import Agent
from groq import Groq
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def handle_agent_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Agent error in {func.__name__}: {e}")
            return {"error": str(e), "status": "failed"}
    return wrapper

class AgentA_DarazScraper(Agent):
    
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
    
    @handle_agent_errors
    def scrape_daraz_product(self, query: str, headless: bool = True, 
                           timeout: int = 30000, max_products: int = 3) -> List[Dict]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            page.set_default_timeout(timeout)
            
            try:
                # Navigate to search page
                encoded_query = quote_plus(query)
                search_url = f"https://www.daraz.pk/catalog/?q={encoded_query}"
                logger.info(f"🔍 Agent A: Searching Daraz for: {query}")
                
                page.goto(search_url, wait_until='networkidle')
                page.wait_for_selector('.gridItem--Yd0sa', timeout=10000)
                
                # Get product cards
                products = []
                product_cards = page.query_selector_all('.gridItem--Yd0sa')[:max_products]
                
                for card in product_cards:
                    try:
                        # Get basic info from card
                        title_el = card.query_selector('.title--wFj93')
                        price_el = card.query_selector('.currency--GVKjl')
                        link_el = card.query_selector('a[href*="/products/"]')
                        rating_el = card.query_selector('[class*="rating"] span')
                        
                        if not (title_el and price_el and link_el):
                            continue
                        
                        # Extract data
                        title = title_el.inner_text()
                        price_text = price_el.inner_text().strip()
                        url = link_el.get_attribute('href')
                        rating = 0
                        
                        if rating_el:
                            try:
                                rating_text = rating_el.inner_text()
                                rating_match = re.search(r'([\d.]+)', rating_text)
                                if rating_match:
                                    rating = float(rating_match.group(1))
                            except:
                                pass
                        
                        # Clean price
                        price_match = re.search(r'[\d,]+', price_text)
                        if price_match:
                            price = float(price_match.group(0).replace(',', ''))
                        else:
                            continue
                        
                        # Build product data
                        product_data = {
                            'source': 'daraz.pk',
                            'title': title,
                            'price_text': price_text,
                            'price_pkr': price,
                            'url': f"https:{url}" if url.startswith('//') else url,
                            'rating_average': rating,
                            'availability': 'In Stock'
                        }
                        
                        products.append(product_data)
                        
                    except Exception as e:
                        logger.error(f"Error processing product card: {e}")
                        continue
                
                browser.close()
                return products if products else [{"error": "No products found", "status": "failed"}]
                
            except Exception as e:
                logger.error(f"Error in Agent A scraping: {e}")
                try:
                    browser.close()
                except:
                    pass
                return [{"error": str(e), "status": "failed"}]

class AgentB_SerperSearch(Agent):
    def __init__(self):
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            raise ValueError("SERPER_API_KEY not found in environment variables")
            
        super().__init__(
            role="Pakistani E-commerce Site Search Agent",
            goal="Search Pakistani e-commerce sites using Serper.dev API",
            backstory="""You are a specialized search agent that uses Serper.dev to find products 
            across Pakistani e-commerce platforms.""",
            verbose=True,
            allow_delegation=False
        )
        self.api_key = api_key
    
    @handle_agent_errors
    def search_pakistani_sites(self, query: str, product_title: str = None) -> List[Dict]:
        """Search Pakistani e-commerce sites via Serper.dev"""
        search_queries = [
            f"{query} site:priceoye.pk OR site:olx.com.pk OR site:telemart.pk",
            f"{product_title if product_title else query} price Pakistan online store",
            f"{query} buy Pakistan ecommerce"
        ]
        
        all_results = []
        
        for search_query in search_queries:
            try:
                logger.info(f"📡 Agent B: Serper query: {search_query[:50]}...")
                
                response = requests.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": self.api_key},
                    json={"q": search_query, "num": 10}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for result in data.get('organic', []):
                        processed = self._process_search_result(result)
                        if processed:
                            all_results.append(processed)
                            
            except Exception as e:
                logger.error(f"Error in search query: {e}")
                continue
        
        # Remove duplicates
        unique_results = []
        seen_urls = set()
        
        for result in all_results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        logger.info(f"✅ Agent B: Found {len(unique_results)} unique results")
        return unique_results
    
    def _process_search_result(self, result: dict) -> Optional[dict]:
        try:
            title = result.get('title', '').replace(' - Price in Pakistan', '')
            snippet = result.get('snippet', '')
            url = result.get('link', '')
            
            # Extract price
            price_match = re.search(r'Rs\.?\s*([\d,]+)', f"{title} {snippet}")
            if not price_match:
                return None
                
            try:
                price = float(price_match.group(1).replace(',', ''))
            except:
                return None
            
            return {
                'source': self._extract_domain(url),
                'title': title,
                'price_text': f"Rs. {price:,.0f}",
                'price_pkr': price,
                'url': url,
                'rating_average': 0,
                'availability': 'In Stock'
            }
            
        except Exception as e:
            logger.error(f"Error processing result: {e}")
            return None
    
    def _extract_domain(self, url: str) -> str:
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.lower()
            domain = domain.replace('www.', '')
            domain = domain.split('.')[0]
            return domain
        except:
            return "unknown"

# Agent factory function
def get_new_agents() -> Dict[str, Agent]:
    return {
        'agent_a_daraz': AgentA_DarazScraper(),
        'agent_b_serper': AgentB_SerperSearch()
    }
