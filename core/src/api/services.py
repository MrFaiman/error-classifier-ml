"""
Search Engine Service
Manages initialization and access to custom ML search engines
"""
from search_engines import CustomTfidfSearchEngine, EnhancedCustomSearchEngine, HybridCustomSearchEngine
from constants import DOCS_ROOT_DIR


class SearchEngineService:
    """Service for managing search engines"""
    
    def __init__(self):
        self.custom_tfidf = None
        self.enhanced_custom = None
        self.hybrid_custom = None
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize all custom search engines"""
        print("Initializing custom ML search engines...")
        
        try:
            self.custom_tfidf = CustomTfidfSearchEngine(docs_root_dir=DOCS_ROOT_DIR)
            print("[OK] Custom TF-IDF Search initialized (100% Custom Implementation)")
        except Exception as e:
            print(f"[ERROR] Custom TF-IDF failed: {e}")
        
        try:
            self.enhanced_custom = EnhancedCustomSearchEngine(docs_root_dir=DOCS_ROOT_DIR)
            print("[OK] Enhanced Custom Search initialized (All Custom ML Algorithms)")
        except Exception as e:
            print(f"[ERROR] Enhanced Custom Search failed: {e}")
        
        try:
            self.hybrid_custom = HybridCustomSearchEngine(
                docs_root_dir=DOCS_ROOT_DIR, 
                tfidf_weight=0.4, 
                bm25_weight=0.6
            )
            print("[OK] Hybrid Custom Search initialized (TF-IDF + BM25 Ranking)")
        except Exception as e:
            print(f"[ERROR] Hybrid Custom Search failed: {e}")
    
    def get_engine(self, method):
        """Get search engine by method name"""
        engines = {
            'CUSTOM_TFIDF': self.custom_tfidf,
            'ENHANCED_CUSTOM': self.enhanced_custom,
            'HYBRID_CUSTOM': self.hybrid_custom
        }
        return engines.get(method)
    
    def get_all_engines(self):
        """Get all available engines"""
        return {
            'custom_tfidf': self.custom_tfidf,
            'enhanced_custom': self.enhanced_custom,
            'hybrid_custom': self.hybrid_custom
        }
    
    def is_healthy(self):
        """Check if at least one engine is available"""
        return any([self.custom_tfidf, self.enhanced_custom, self.hybrid_custom])


# Global service instance
search_service = SearchEngineService()
