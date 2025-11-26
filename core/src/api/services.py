"""
Search Engine Service
Manages initialization and access to custom ML search engines
"""
from search_engines import HybridCustomSearchEngine
from constants import DOCS_ROOT_DIR, MONGODB_CONNECTION_STRING


class SearchEngineService:
    """Service for managing search engines"""
    
    def __init__(self):
        self.hybrid_custom = None
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize Hybrid Custom search engine"""
        print("Initializing Hybrid Custom search engine...")
        
        try:
            self.hybrid_custom = HybridCustomSearchEngine(
                docs_root_dir=DOCS_ROOT_DIR, 
                tfidf_weight=0.4, 
                bm25_weight=0.6,
                mongo_connection_string=MONGODB_CONNECTION_STRING
            )
            print("[OK] Hybrid Custom Search initialized (TF-IDF + BM25 + Adaptive Feedback)")
        except Exception as e:
            print(f"[ERROR] Hybrid Custom Search failed: {e}")
    
    def get_engine(self, method):
        """Get search engine by method name"""
        # Always return hybrid for any method
        return self.hybrid_custom
    
    def get_all_engines(self):
        """Get all available engines"""
        return {
            'hybrid_custom': self.hybrid_custom
        }
    
    def is_healthy(self):
        """Check if engine is available"""
        return self.hybrid_custom is not None


# Global service instance
search_service = SearchEngineService()
