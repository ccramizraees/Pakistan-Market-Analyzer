from crewai import Task
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def create_task_a_daraz_scraping(agents: Dict, query: str, **kwargs) -> Task:
    task_description = f"""
    **TASK A: DARAZ PRODUCT SCRAPING**
    
    Search and extract comprehensive product information from Daraz.pk for the query: "{query}"
    
    **Specific Requirements:**
    1. Navigate to Daraz.pk and search for: "{query}"
    2. Select product at index: {kwargs.get('index', 0)}
    3. Extract complete product details:
       - Product title and description
       - Price information (PKR)
       - Seller information
       - Product ratings and reviews
       - Product specifications
       - Availability status
    
    **Browser Configuration:**
    - Headless mode: {kwargs.get('headless', False)}
    - Timeout: {kwargs.get('timeout', 30000)}ms
    - User agent: Desktop Chrome
    
    **Expected Output:**
    Structured JSON with product data including title, price_pkr, seller, rating_average, url, and status.
    
    **Error Handling:**
    If scraping fails, return error details with fallback recommendations.
    """
    
    return Task(
        description=task_description,
        agent=agents['agent_a_daraz'],
        expected_output="JSON object with Daraz product data including title, price, seller, and URL"
    )


def create_task_b_serper_search_and_process(agents: Dict, query: str, **kwargs) -> Task:
    
    task_description = f"""
    **TASK B: PAKISTANI MARKETPLACE SEARCH + DIRECT PROCESSING**
    
    Search Pakistani e-commerce sites using Serper.dev API and process results directly for: "{query}"
    
    **Search Strategy:**
    1. Use Serper.dev API with Pakistani geo-targeting (gl=pk)
    2. Target specific sites: PriceOye.pk, OLX.com.pk, Telemart.pk, Shophive.pk
    3. Use multiple query variations for comprehensive coverage
    4. Maximum results per platform: {kwargs.get('max_results', 10)}
    
    **Direct Processing Requirements:**
    1. Extract product information from search results:
       - Product titles and descriptions
       - Price information (convert to PKR if needed)
       - Platform/website identification
       - Product URLs
       - Availability indicators
    
    2. Price extraction using regex patterns:
       - Rs. 50,000 format
       - PKR 50,000 format  
       - 50,000 PKR format
       - Price: Rs. 50,000 format
    
    3. Data structure requirements:
       - title: Product name
       - price_text: Original price text
       - price_numeric: Numeric price in PKR
       - platform: Website name (PriceOye, OLX, etc.)
       - url: Product page URL
       - confidence: Processing confidence score
    
    **Pakistani Market Focus:**
    - Prioritize local Pakistani sellers
    - Focus on PKR currency
    - Consider PTA approval for electronics
    - Account for local warranty vs international
    
    **Quality Control:**
    - Remove duplicate results
    - Filter out invalid/irrelevant results
    - Assign confidence scores based on data quality
    
    **Expected Output:**
    JSON object with processed product results including titles, prices (PKR), platforms, and URLs.
    """
    
    # This task depends on Task A output (product title from Daraz)
    return Task(
        description=task_description,
        agent=agents['agent_b_serper'],
        expected_output="JSON with processed product results from Pakistani e-commerce sites",
        context=[] # Will be set dynamically with Task A results
    )


def create_task_d_report_generation(agents: Dict, query: str, **kwargs) -> Task:
    
    task_description = f"""
    **TASK D: COMPREHENSIVE PRICE COMPARISON REPORT**
    
    Generate a detailed Pakistani e-commerce comparison report for: "{query}"
    
    **Data Sources:**
    1. Daraz product data from Task A
    2. Processed marketplace results from Task B (direct processing, no Task C)
    
    **Report Structure:**
    1. **Executive Summary**
       - Total products found across platforms
       - Price range analysis (min, max, average)
       - Key findings and recommendations
    
    2. **Detailed Price Comparison**
       - Platform-by-platform breakdown
       - Price rankings (lowest to highest)
       - Value-for-money analysis
    
    3. **Platform Analysis**
       - Daraz.pk: Official retailer analysis
       - PriceOye.pk: Electronics specialist insights
       - OLX.pk: Used/new marketplace considerations
       - Telemart.pk: Appliance and electronics focus
       - Shophive.pk: General marketplace analysis
    
    4. **Pakistani Market Insights**
       - Local vs international warranty considerations
       - PTA approval status (for electronics)
       - Shipping and delivery analysis
       - Payment method availability
       - Customer service and return policies
    
    5. **Best Value Recommendations**
       - Cheapest option with analysis
       - Best value-for-money recommendation
       - Premium option analysis
       - Budget-friendly alternatives
    
    6. **Buying Guide**
       - What to check before purchasing
       - Red flags to avoid
       - Optimal purchasing timing
       - Negotiation tips (for applicable platforms)
    
    **Technical Requirements:**
    1. Use Groq LLM (llama-3.1-8b-instant) for analysis
    2. Generate both structured data and markdown report
    3. Save report to data/reports/ directory
    4. Include metadata and timestamp
    
    **Pakistani Context:**
    - All prices in Pakistani Rupees (PKR)
    - Consider local market conditions
    - Account for seasonal price variations
    - Include relevant consumer protection advice
    - Consider regional availability differences
    
    **Output Formats:**
    1. Structured JSON with best deals, insights, and recommendations
    2. Markdown report file saved to disk
    3. Processing metadata and statistics
    
    **Error Handling:**
    If LLM processing fails, generate fallback report with available data.
    """
    
    # This task depends on both Task A and Task B results
    return Task(
        description=task_description,
        agent=agents['agent_d_report'],
        expected_output="Comprehensive comparison report with best deals, market insights, and buying recommendations",
        context=[] # Will be set dynamically with Task A and B results
    )


def get_new_tasks(agents: Dict, query: str, **kwargs) -> list:
    
    logger.info(f"🔧 Creating task workflow for: {query}")
    
    # Task A: Daraz Scraping
    task_a = create_task_a_daraz_scraping(agents, query, **kwargs)
    
    # Task B: Serper Search + Direct Processing (replaces both old Task B and Task C)
    task_b = create_task_b_serper_search_and_process(agents, query, **kwargs)
    
    # Task D: Report Generation
    task_d = create_task_d_report_generation(agents, query, **kwargs)
    
    # Set up task dependencies
    # Task B depends on Task A (uses Daraz product title for better search)
    task_b.context = [task_a]
    
    # Task D depends on both Task A and Task B
    task_d.context = [task_a, task_b]
    
    logger.info("📋 Task workflow created:")
    logger.info("   Task A: Daraz Product Scraping")
    logger.info("   Task B: Serper Search + Direct Processing (NO Agent C)")
    logger.info("   Task D: Report Generation")
    logger.info("   Dependencies: A → B → D")
    
    return [task_a, task_b, task_d]
