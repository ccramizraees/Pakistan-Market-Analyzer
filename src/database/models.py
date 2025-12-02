import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class MarketplaceDB:    
    def __init__(self, db_path: str = "data/marketplace.db"):
        """Initialize database connection."""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_tables()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_tables(self):
        with self.get_connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS queries (
                    id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT DEFAULT 'pending'
                );
                
                CREATE TABLE IF NOT EXISTS raw_products (
                    id TEXT PRIMARY KEY,
                    query_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    title TEXT,
                    price_pkr REAL,
                    price_text TEXT,
                    description TEXT,
                    rating_average REAL,
                    seller TEXT,
                    availability TEXT,
                    url TEXT,
                    fetched_at TEXT,
                    raw_data TEXT,
                    FOREIGN KEY (query_id) REFERENCES queries (id)
                );
                
                CREATE TABLE IF NOT EXISTS normalized_products (
                    id TEXT PRIMARY KEY,
                    query_id TEXT NOT NULL,
                    raw_product_id TEXT NOT NULL,
                    title TEXT,
                    brand TEXT,
                    model TEXT,
                    capacity TEXT,
                    pta_status TEXT,
                    price_pkr REAL,
                    seller TEXT,
                    rating_average REAL,
                    source TEXT,
                    url TEXT,
                    fetched_at TEXT,
                    comparable_cluster_id TEXT,
                    match_confidence REAL,
                    FOREIGN KEY (query_id) REFERENCES queries (id),
                    FOREIGN KEY (raw_product_id) REFERENCES raw_products (id)
                );
                
                CREATE TABLE IF NOT EXISTS price_analysis (
                    id TEXT PRIMARY KEY,
                    query_id TEXT NOT NULL,
                    cluster_id TEXT NOT NULL,
                    min_price REAL,
                    max_price REAL,
                    avg_price REAL,
                    cheapest_vendor TEXT,
                    cheapest_product_id TEXT,
                    product_count INTEGER,
                    analysis_date TEXT,
                    FOREIGN KEY (query_id) REFERENCES queries (id)
                );
                
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    query_id TEXT NOT NULL,
                    report_type TEXT NOT NULL,
                    file_path TEXT,
                    created_at TEXT,
                    FOREIGN KEY (query_id) REFERENCES queries (id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_queries_created_at ON queries(created_at);
                CREATE INDEX IF NOT EXISTS idx_raw_products_query_id ON raw_products(query_id);
                CREATE INDEX IF NOT EXISTS idx_normalized_products_cluster ON normalized_products(comparable_cluster_id);
                CREATE INDEX IF NOT EXISTS idx_price_analysis_cluster ON price_analysis(cluster_id);
            ''')
    
    def create_query(self, query: str) -> str:
        query_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO queries (id, query, created_at) VALUES (?, ?, ?)",
                (query_id, query, datetime.utcnow().isoformat())
            )
        return query_id
    
    def save_raw_products(self, query_id: str, products: List[Dict[str, Any]]) -> List[str]:
        product_ids = []
        with self.get_connection() as conn:
            for product in products:
                product_id = str(uuid.uuid4())
                product_ids.append(product_id)
                
                conn.execute('''
                    INSERT INTO raw_products 
                    (id, query_id, source, title, price_pkr, price_text, description, 
                     rating_average, seller, availability, url, fetched_at, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product_id,
                    query_id,
                    product.get('source', 'unknown'),
                    product.get('title'),
                    product.get('price_pkr'),
                    product.get('price_text'),
                    product.get('description'),
                    product.get('rating_average'),
                    product.get('seller'),
                    product.get('availability'),
                    product.get('url'),
                    product.get('fetched_at'),
                    json.dumps(product)
                ))
        
        return product_ids
    
    def save_normalized_products(self, query_id: str, products: List[Dict[str, Any]]) -> List[str]:
        product_ids = []
        with self.get_connection() as conn:
            for product in products:
                product_id = str(uuid.uuid4())
                product_ids.append(product_id)
                
                conn.execute('''
                    INSERT INTO normalized_products 
                    (id, query_id, raw_product_id, title, brand, model, capacity, pta_status,
                     price_pkr, seller, rating_average, source, url, fetched_at, 
                     comparable_cluster_id, match_confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product_id,
                    query_id,
                    product.get('raw_product_id', ''),
                    product.get('title'),
                    product.get('brand'),
                    product.get('model'),
                    product.get('capacity'),
                    product.get('pta_status'),
                    product.get('price_pkr'),
                    product.get('seller'),
                    product.get('rating_average'),
                    product.get('source'),
                    product.get('url'),
                    product.get('fetched_at'),
                    product.get('comparable_cluster_id'),
                    product.get('match_confidence')
                ))
        
        return product_ids
    
    def save_price_analysis(self, query_id: str, analysis: List[Dict[str, Any]]) -> List[str]:
        analysis_ids = []
        with self.get_connection() as conn:
            for item in analysis:
                analysis_id = str(uuid.uuid4())
                analysis_ids.append(analysis_id)
                
                conn.execute('''
                    INSERT INTO price_analysis 
                    (id, query_id, cluster_id, min_price, max_price, avg_price,
                     cheapest_vendor, cheapest_product_id, product_count, analysis_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis_id,
                    query_id,
                    item.get('cluster_id'),
                    item.get('min_price'),
                    item.get('max_price'),
                    item.get('avg_price'),
                    item.get('cheapest_vendor'),
                    item.get('cheapest_product_id'),
                    item.get('product_count'),
                    datetime.utcnow().isoformat()
                ))
        
        return analysis_ids
    
    def save_report(self, query_id: str, report_type: str, file_path: str) -> str:
        report_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO reports (id, query_id, report_type, file_path, created_at) VALUES (?, ?, ?, ?, ?)",
                (report_id, query_id, report_type, file_path, datetime.utcnow().isoformat())
            )
        return report_id
    
    def get_query_data(self, query_id: str) -> Dict[str, Any]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            
            query_info = conn.execute(
                "SELECT * FROM queries WHERE id = ?", (query_id,)
            ).fetchone()
            
            raw_products = conn.execute(
                "SELECT * FROM raw_products WHERE query_id = ?", (query_id,)
            ).fetchall()
            
            normalized_products = conn.execute(
                "SELECT * FROM normalized_products WHERE query_id = ?", (query_id,)
            ).fetchall()
            
            price_analysis = conn.execute(
                "SELECT * FROM price_analysis WHERE query_id = ?", (query_id,)
            ).fetchall()
            
            reports = conn.execute(
                "SELECT * FROM reports WHERE query_id = ?", (query_id,)
            ).fetchall()
            
            return {
                'query': dict(query_info) if query_info else None,
                'raw_products': [dict(row) for row in raw_products],
                'normalized_products': [dict(row) for row in normalized_products],
                'price_analysis': [dict(row) for row in price_analysis],
                'reports': [dict(row) for row in reports]
            }
    
    def update_query_status(self, query_id: str, status: str):
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE queries SET status = ? WHERE id = ?",
                (status, query_id)
            )
    
    def get_recent_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM queries ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(row) for row in rows]
