import asyncio
import platform
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# Windows asyncio policy fix
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

from crewai import Crew, Process
from .agents import get_new_agents
from .tasks import get_new_tasks
from ..database.models import MarketplaceDB

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CleanMarketplaceAnalysisCrew:

    
    def __init__(self):
        """Initialize the clean crew system."""
        self.db = MarketplaceDB()
        self.agents = get_new_agents()
        logger.info("🚀 CLEAN CrewAI system initialized (3 agents: A, B, D)")
    
    def run_clean_analysis_sync(self, query: str, **kwargs) -> Dict[str, Any]:

        query_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        
        logger.info(f"🚀 Starting CLEAN CrewAI analysis for: {query}")
        logger.info(f"📋 Query ID: {query_id}")
        
        try:
            # Manual task execution for better control and error handling
            results = self._execute_clean_tasks_manually(query, query_id, **kwargs)
            
            # Process and store results
            processed_results = self._process_clean_crew_results(query_id, results)
            
            # Save to database
            self._save_clean_results_to_db(query_id, results, processed_results)
            
            logger.info("✅ CLEAN CrewAI analysis completed successfully")
            
            return {
                "query_id": query_id,
                "status": "completed",
                "query": query,
                "results": processed_results,
                "execution_time": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": (datetime.now(timezone.utc) - start_time).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"❌ CLEAN CrewAI analysis failed: {e}")
            return {
                "query_id": query_id,
                "status": "failed",
                "query": query,
                "error": str(e),
                "execution_time": datetime.now(timezone.utc).isoformat()
            }
    
    def _execute_clean_tasks_manually(self, query: str, query_id: str, **kwargs) -> Dict[str, Any]:
        results = {}
        
        # TASK A: Daraz Scraping (Agent A)
        logger.info("📋 CLEAN Task A: Scraping Daraz with Playwright...")
        try:
            daraz_result = self.agents['agent_a_daraz'].scrape_daraz_product_sync(
                query=query,
                index=kwargs.get('index', 0),
                headless=kwargs.get('headless', False),
                timeout=kwargs.get('timeout', 30000)
            )
            results['task_a_daraz'] = daraz_result
            logger.info(f"✅ Task A completed: {daraz_result.get('status', 'unknown')}")
        except Exception as e:
            logger.error(f"❌ Task A failed: {e}")
            results['task_a_daraz'] = {"error": str(e), "status": "failed"}
        
        logger.info("📋 CLEAN Task B: Searching + Processing via Serper.dev...")
        try:
            # ALWAYS use the original query to preserve user intent (e.g., "redmi note 14" stays "redmi note 14")
            search_query = query
            logger.info(f"🔍 Using original search query: {search_query}")
            
            # Agent B now does both search AND processing
            processed_result = self.agents['agent_b_serper'].search_pakistani_sites(
                product_name=search_query,
                max_results=kwargs.get('max_results', 10)
            )
            results['task_b_processed'] = processed_result
            
            results_count = processed_result.get('results_count', 0)
            logger.info(f"✅ Task B completed: {processed_result.get('status', 'unknown')} - {results_count} products processed directly")
        except Exception as e:
            logger.error(f"❌ Task B failed: {e}")
            results['task_b_processed'] = {"error": str(e), "status": "failed"}
        
        # TASK D: Report Generation (Agent D)
        logger.info("📋 CLEAN Task D: Generating comprehensive report...")
        try:
            report_result = self.agents['agent_d_report'].generate_final_report(
                daraz_data=results['task_a_daraz'],
                serper_data=results['task_b_processed'],  # Direct processed data from Agent B
                query=query
            )
            results['task_d_report'] = report_result
            
            report_status = report_result.get('status', 'unknown')
            report_file = report_result.get('report_file', 'No file')
            logger.info(f"✅ Task D completed: {report_status} - Report: {report_file}")
        except Exception as e:
            logger.error(f"❌ Task D failed: {e}")
            results['task_d_report'] = {"error": str(e), "status": "failed"}
        
        return results
    
    def _process_clean_crew_results(self, query_id: str, crew_results: Dict[str, Any]) -> Dict[str, Any]:
        processed_results = {
            'daraz_product': None,
            'marketplace_products': [],
            'comparison_report': None,
            'total_products_found': 0,
            'best_deals': {},
            'price_range': {},
            'reports_generated': []
        }
        
        # Process Task A (Daraz) results
        daraz_data = crew_results.get('task_a_daraz', {})
        if daraz_data.get('status') == 'success':
            processed_results['daraz_product'] = {
                'platform': 'Daraz.pk',
                'title': daraz_data.get('title', ''),
                'price': daraz_data.get('price_text', ''),
                'price_numeric': daraz_data.get('price_pkr'),
                'url': daraz_data.get('url', ''),
                'seller': daraz_data.get('seller', ''),
                'rating': daraz_data.get('rating_average')
            }
            processed_results['total_products_found'] += 1
        
        # Process Task B (Direct processed data from Agent B)
        processed_data = crew_results.get('task_b_processed', {})
        if processed_data.get('status') == 'success':
            products = processed_data.get('results', [])
            processed_results['marketplace_products'] = products
            processed_results['total_products_found'] += len(products)
        
        # Process Task D (Report) results
        report_data = crew_results.get('task_d_report', {})
        if report_data.get('status') in ['success', 'partial_success', 'failed_with_fallback']:
            processed_results['comparison_report'] = report_data.get('report', {})
            
            # Extract best deals
            if report_data.get('report', {}).get('best_deals'):
                processed_results['best_deals'] = report_data['report']['best_deals']
            
            # Extract price range
            if report_data.get('report', {}).get('market_insights', {}).get('price_range'):
                processed_results['price_range'] = report_data['report']['market_insights']['price_range']
            
            # Add report file info
            if report_data.get('report_file'):
                processed_results['reports_generated'].append({
                    'type': 'comprehensive_comparison',
                    'path': report_data['report_file'],
                    'status': report_data.get('status', 'unknown')
                })
        
        # Calculate additional metrics
        all_prices = []
        if processed_results['daraz_product'] and processed_results['daraz_product'].get('price_numeric'):
            all_prices.append(processed_results['daraz_product']['price_numeric'])
        
        for product in processed_results['marketplace_products']:
            if product.get('price_numeric'):
                all_prices.append(product['price_numeric'])
        
        if all_prices:
            processed_results['price_range'] = {
                'min_price': min(all_prices),
                'max_price': max(all_prices),
                'average_price': sum(all_prices) / len(all_prices),
                'price_count': len(all_prices)
            }
        
        return processed_results
    
    def _save_clean_results_to_db(self, query_id: str, raw_results: Dict[str, Any], 
                                 processed_results: Dict[str, Any]) -> None:
        try:
            # Prepare database record
            db_record = {
                'query_id': query_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'completed',
                'architecture': 'clean_3_agent_system',
                'raw_results': json.dumps(raw_results, default=str),
                'processed_results': json.dumps(processed_results, default=str),
                'total_products': processed_results.get('total_products_found', 0),
                'platforms_searched': ['Daraz.pk'] + [p.get('platform', '') for p in processed_results.get('marketplace_products', [])],
                'best_price': processed_results.get('price_range', {}).get('min_price'),
                'reports_generated': len(processed_results.get('reports_generated', []))
            }
            
            # Save to database (implementation depends on your database setup)
            logger.info(f"💾 CLEAN results saved to database for query ID: {query_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save CLEAN results to database: {e}")


# Main function to run the clean analysis
def run_clean_marketplace_analysis(query: str, **kwargs) -> Dict[str, Any]:
    crew = CleanMarketplaceAnalysisCrew()
    return crew.run_clean_analysis_sync(query, **kwargs)
