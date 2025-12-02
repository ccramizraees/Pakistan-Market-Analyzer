"""
Pakistani E-commerce Price Comparison - Streamlit UI
Modern SaaS-style interface for comparing prices across Pakistani marketplaces.
"""
import streamlit as st
import asyncio
import os
from datetime import datetime
import pandas as pd
from pathlib import Path
import json
from rich.console import Console
import plotly.express as px
from src.crew.crew import run_clean_marketplace_analysis

# Page config
st.set_page_config(
    page_title="Pakistani Price Tracker 🛍️",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern SaaS look
st.markdown("""
<style>
    /* Modern color scheme */
    :root {
        --primary-color: #FF4B4B;
        --secondary-color: #4B4BFF;
        --background-color: #FFFFFF;
        --text-color: #31333F;
        --card-bg: #F8F9FA;
        --border-color: #E1E5E9;
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: var(--text-color);
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Fix metric cards visibility */
    div[data-testid="metric-container"] {
        background-color: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }
    
    div[data-testid="metric-container"] > div {
        color: var(--text-color) !important;
    }
    
    div[data-testid="metric-container"] label {
        color: #666 !important;
        font-weight: 500 !important;
    }
    
    div[data-testid="metric-container"] [data-testid="metric-value"] {
        color: var(--primary-color) !important;
        font-weight: bold !important;
        font-size: 1.5rem !important;
    }
    
    /* Card-like containers */
    div.stDataFrame {
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: white;
        border: 1px solid var(--border-color);
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 20px;
        font-weight: 500;
        border: 1px solid var(--border-color);
    }
    
    /* Expander styling - Fix for reports section */
    div[data-testid="stExpander"] {
        background-color: white !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
    }
    
    div[data-testid="stExpander"] > div:first-child {
        background-color: var(--card-bg) !important;
        border-radius: 10px 10px 0 0 !important;
        padding: 0.75rem 1rem !important;
    }
    
    div[data-testid="stExpander"] > div:last-child {
        background-color: white !important;
        padding: 1rem !important;
        border-radius: 0 0 10px 10px !important;
    }
    
    /* Success/Info messages */
    div[data-testid="stAlert"] {
        border-radius: 10px;
    }
    
    /* Improve table styling */
    div[data-testid="stDataFrame"] table {
        border-collapse: separate !important;
        border-spacing: 0 !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
    }
    
    div[data-testid="stDataFrame"] th {
        background-color: var(--card-bg) !important;
        font-weight: 600 !important;
        color: var(--text-color) !important;
        border-bottom: 2px solid var(--border-color) !important;
    }
    
    div[data-testid="stDataFrame"] td {
        border-bottom: 1px solid #F0F0F0 !important;
    }
</style>
""", unsafe_allow_html=True)

def load_recent_searches():
    """Load recent searches from JSON file."""
    try:
        path = Path("data/recent_searches.json")
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_recent_search(query, result):
    """Save search to recent searches."""
    try:
        searches = load_recent_searches()
        searches.insert(0, {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "results": result
        })
        # Keep only last 10 searches
        searches = searches[:10]
        
        path = Path("data/recent_searches.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(searches, f)
    except Exception as e:
        st.error(f"Failed to save search: {e}")

def display_price_comparison(results):
    """Display price comparison results in a modern way."""
    if not results or results.get('status') != 'completed':
        st.error("❌ Analysis failed to complete successfully")
        if results and results.get('error'):
            st.error(f"Error: {results['error']}")
        return
    
    results_data = results.get('results', {})
    
    # Summary metrics in a row with better styling
    st.subheader("📊 Analysis Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_products = results_data.get('total_products_found', 0)
        st.metric(
            label="🔍 Products Found", 
            value=str(total_products),
            help="Total number of products found across all platforms"
        )
    
    with col2:
        query_id = results.get('query_id', 'N/A')
        st.metric(
            label="🆔 Query ID", 
            value=query_id[:8] + "..." if len(query_id) > 8 else query_id,
            help=f"Full ID: {query_id}"
        )
    
    with col3:
        duration = results.get('duration_seconds', 0)
        st.metric(
            label="⏱️ Duration", 
            value=f"{duration:.1f}s",
            help="Total analysis time"
        )
    
    with col4:
        execution_time = results.get('execution_time', 'N/A')
        if execution_time != 'N/A':
            # Format timestamp to be more readable
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(execution_time.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%H:%M:%S")
            except:
                formatted_time = execution_time[:10]
        else:
            formatted_time = 'N/A'
        
        st.metric(
            label="🕐 Completed At", 
            value=formatted_time,
            help=f"Full timestamp: {execution_time}"
        )
    
    # Show detailed results
    st.markdown("---")
    
    # Daraz Product Details - Clean and focused
    daraz_product = results_data.get('daraz_product')
    if daraz_product:
        st.subheader("🛒 Featured Product from Daraz.pk")
        
        # Create a nice product card layout
        card_col1, card_col2 = st.columns([3, 1])
        
        with card_col1:
            # Clean title
            title = daraz_product.get('title', 'N/A')
            if title and len(title) > 100:
                title = title[:100] + "..."
            st.markdown(f"### 📦 {title}")
            
            # Price with emphasis
            price = daraz_product.get('price', 'N/A')
            if price:
                st.markdown(f"### 💰 **{price}**")
            
            # Additional info in columns
            info_col1, info_col2 = st.columns(2)
            
            with info_col1:
                seller = daraz_product.get('seller', 'N/A')
                if seller and seller != 'N/A':
                    st.markdown(f"👤 **Seller:** {seller}")
            
            with info_col2:
                rating = daraz_product.get('rating')
                if rating:
                    stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
                    st.markdown(f"⭐ **Rating:** {rating}/5 {stars}")
        
        with card_col2:
            if daraz_product.get('url'):
                st.link_button(
                    "🔗 View on Daraz",
                    daraz_product['url'],
                    use_container_width=True
                )
        
        st.markdown("---")
    
    # Price comparison with enhanced table
    st.subheader("💰 Price Comparison Across Platforms")
    cheapest_options = results_data.get('cheapest_options', [])
    marketplace_products = results_data.get('marketplace_products', [])
    
    # Combine all products for display
    all_products = []
    
    # Add Daraz product first (if available)
    if daraz_product and daraz_product.get('price_numeric'):
        all_products.append({
            'Platform': '🛒 Daraz.pk',
            'Price (PKR)': f"Rs. {daraz_product.get('price_numeric'):,}",
            'price_numeric': daraz_product.get('price_numeric'),
            'url': daraz_product.get('url', ''),
            'title': daraz_product.get('title', ''),
            'source': 'daraz'
        })
    
    # Add marketplace products
    for product in marketplace_products:
        if product.get('price_numeric'):
            platform_name = product.get('platform', 'Unknown')
            # Add emoji based on platform
            if 'olx' in platform_name.lower():
                platform_name = f"🔄 {platform_name}"
            elif 'priceoye' in platform_name.lower():
                platform_name = f"💻 {platform_name}"
            elif 'telemart' in platform_name.lower():
                platform_name = f"📱 {platform_name}"
            else:
                platform_name = f"🏪 {platform_name}"
                
            all_products.append({
                'Platform': platform_name,
                'Price (PKR)': f"Rs. {product.get('price_numeric'):,}",
                'price_numeric': product.get('price_numeric'),
                'url': product.get('url', ''),
                'title': product.get('title', ''),
                'source': 'marketplace'
            })
    
    if all_products:
        # Sort by price (lowest to highest)
        all_products.sort(key=lambda x: x['price_numeric'])
        
        # Create the main comparison table like in the report
        st.markdown("### � **Price Comparison (Lowest to Highest)**")
        
        # Create clean DataFrame for display
        display_data = []
        for i, product in enumerate(all_products):
            rank = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
            savings = product['price_numeric'] - all_products[0]['price_numeric']
            savings_text = "**Best Price!**" if savings == 0 else f"+Rs. {savings:,}"
            
            display_data.append({
                'Rank': rank,
                'Platform': product['Platform'],
                'Price (PKR)': product['Price (PKR)'],
                'Difference': savings_text
            })
        
        # Display as a nice table
        df_display = pd.DataFrame(display_data)
        
        st.dataframe(
            df_display,
            column_config={
                "Rank": st.column_config.TextColumn("�", width="small"),
                "Platform": st.column_config.TextColumn("Platform", width="medium"),
                "Price (PKR)": st.column_config.TextColumn("� Price", width="medium"),
                "Difference": st.column_config.TextColumn("💡 Savings", width="medium"),
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Create price comparison chart
        if len(all_products) > 1:
            # Prepare data for chart
            chart_data = pd.DataFrame([
                {'Platform': p['Platform'].split(' ', 1)[-1], 'Price': p['price_numeric']} 
                for p in all_products
            ])
            
            fig = px.bar(
                chart_data,
                x='Platform',
                y='Price',
                title="Price Comparison Across Pakistani E-commerce Platforms",
                color='Platform',
                labels={'Price': 'Price (PKR)', 'Platform': 'Platform'},
                template="plotly_white",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(
                showlegend=False,
                height=400,
                xaxis_tickangle=-45,
                title_font_size=16,
                title_x=0.5
            )
            # Add price labels on bars
            fig.update_traces(
                texttemplate='Rs. %{y:,}',
                textposition='outside'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Price insights with better formatting
        if len(all_products) > 1:
            st.markdown("### 💡 **Price Insights**")
            col1, col2, col3 = st.columns(3)
            
            min_price = all_products[0]['price_numeric']
            max_price = all_products[-1]['price_numeric']
            avg_price = sum(p['price_numeric'] for p in all_products) / len(all_products)
            
            with col1:
                st.metric(
                    "💸 Lowest Price", 
                    f"Rs. {min_price:,}",
                    help=f"Available at {all_products[0]['Platform']}"
                )
            with col2:
                st.metric(
                    "💰 Highest Price", 
                    f"Rs. {max_price:,}",
                    help=f"Available at {all_products[-1]['Platform']}"
                )
            with col3:
                price_diff = max_price - min_price
                savings_percent = (price_diff / max_price * 100) if max_price > 0 else 0
                st.metric(
                    "📈 Max Savings", 
                    f"Rs. {price_diff:,}",
                    delta=f"-{savings_percent:.1f}%",
                    help="You can save this much by choosing the cheapest option"
                )
    else:
        st.warning("⚠️ No price comparison data available from the search results")
    
    # Market insights and reports
    st.markdown("---")
    
    # Reports section - Enhanced
    reports = results_data.get('reports_generated', [])
    if reports:
        st.subheader("📄 Generated Reports & Analysis")
        for i, report in enumerate(reports):
            report_type = report.get('type', f'Report {i+1}')
            with st.expander(f"📝 {report_type.replace('_', ' ').title()}", expanded=(i == 0)):
                
                # Show report metadata
                col1, col2 = st.columns([3, 1])
                with col1:
                    if 'path' in report:
                        st.info(f"📁 Saved to: `{report['path']}`")
                with col2:
                    if 'status' in report:
                        status = report['status']
                        if status == 'success':
                            st.success("✅ Generated")
                        elif status == 'partial_success':
                            st.warning("⚠️ Partial")
                        else:
                            st.error("❌ Failed")
                
                # Show report content
                content = report.get('content_preview', 'No preview available')
                if content and len(content) > 100:
                    st.markdown(content)
                    
                    # Download button
                    if 'path' in report:
                        try:
                            report_path = Path(report['path'])
                            if report_path.exists():
                                with open(report_path, 'r', encoding='utf-8') as f:
                                    full_content = f.read()
                                st.download_button(
                                    "📥 Download Full Report",
                                    full_content,
                                    file_name=report_path.name,
                                    mime="text/markdown",
                                    key=f"download_{i}"
                                )
                        except Exception as e:
                            st.error(f"Could not load report file: {e}")
                else:
                    st.text(content or "No content available")
    
    # Additional insights
    comparison_report = results_data.get('comparison_report', {})
    if comparison_report:
        st.subheader("🎯 Key Insights")
        
        # Best deals
        best_deals = results_data.get('best_deals', {})
        if best_deals:
            st.success("🏆 **Best Deal Found:**")
            for platform, deal in best_deals.items():
                st.write(f"• **{platform}**: {deal}")
        
        # Market insights
        market_insights = comparison_report.get('market_insights', {})
        if market_insights:
            st.info("💡 **Market Analysis:**")
            for insight, value in market_insights.items():
                if isinstance(value, str):
                    st.write(f"• **{insight.replace('_', ' ').title()}**: {value}")
    
    # Database info
    st.markdown("---")
    st.caption(f"💾 Analysis data saved to database with ID: {results.get('query_id', 'N/A')}")
    st.caption("📊 Data includes all scraped products, pricing trends, and market analysis")

def check_api_configuration():
    """Check if required API keys are configured."""
    issues = []
    
    # Check Serper API
    if not os.getenv("SERPER_API_KEY"):
        issues.append("🔑 SERPER_API_KEY not found - Marketplace search will be limited")
    
    # Check Groq API (if used)
    if not os.getenv("GROQ_API_KEY"):
        issues.append("🤖 GROQ_API_KEY not found - AI analysis features may be limited")
    
    return issues

def main():
    """Main Streamlit app."""
    # Check API configuration
    api_issues = check_api_configuration()
    if api_issues:
        with st.sidebar:
            st.warning("⚠️ **API Configuration Issues:**")
            for issue in api_issues:
                st.write(f"• {issue}")
            st.write("Add missing API keys to your `.env` file for full functionality.")
    
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Search Settings")
        max_results = st.slider(
            "Maximum results per marketplace",
            min_value=1,
            max_value=10,
            value=3,
            help="Number of products to fetch from each marketplace"
        )
        
        headless = not st.checkbox(
            "Show browser while scraping",
            value=False,
            help="Enable to see the browser automation in action"
        )
        
        timeout = st.slider(
            "Timeout per page (seconds)",
            min_value=10,
            max_value=60,
            value=30,
            help="Maximum time to wait for each page to load"
        ) * 1000  # Convert to milliseconds
        
        with st.expander("Advanced Options"):
            index = st.number_input(
                "Daraz result index",
                min_value=0,
                max_value=10,
                value=0,
                help="Which Daraz result to analyze in detail"
            )
    
    # Main content
    st.title("🛍️ Pakistani Price Tracker")
    st.caption("Compare prices across major Pakistani e-commerce platforms")
    
    # Search bar
    query = st.text_input(
        "🔍 Search for products",
        placeholder="e.g., iPhone 15, Dell Laptop, Nike Air Max",
        help="Enter any product name to compare prices"
    )
    
    # Recent searches
    recent_searches = load_recent_searches()
    if recent_searches:
        st.caption("Recent searches")
        for search in recent_searches[:5]:
            if st.button(
                f"🔄 {search['query']} ({search['timestamp'][:10]})",
                key=f"recent_{search['query']}_{search['timestamp']}"
            ):
                query = search['query']
    
    # Search button
    if query:
        with st.spinner("🔍 Analyzing prices across Pakistani marketplaces..."):
            try:
                # Run analysis (now synchronous)
                result = run_clean_marketplace_analysis(
                    query=query,
                    max_results=max_results,
                    headless=headless,
                    timeout=timeout,
                    index=index
                )
                
                # Save search
                save_recent_search(query, result)
                
                # Display results
                display_price_comparison(result)
                
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
    else:
        # Welcome message for first-time users
        st.info(
            "👋 Welcome to Pakistani Price Tracker!\n\n"
            "Enter a product name above to compare prices across:"
            "\n- Daraz.pk"
            "\n- PriceOye"
            "\n- OLX Pakistan"
            "\n- Telemart"
            "\n- And more!"
        )

if __name__ == "__main__":
    main()
