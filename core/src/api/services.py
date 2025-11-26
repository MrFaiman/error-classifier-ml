"""
Search Engine Service
Manages initialization and access to custom ML search engines
"""
from search_engines import HybridCustomSearchEngine
from constants import DOCS_ROOT_DIR, MONGODB_CONNECTION_STRING
from algorithms import get_explainer
from utils import get_logger

logger = get_logger(__name__)


class SearchEngineService:
    """Service for managing search engines"""
    
    def __init__(self):
        self.hybrid_custom = None
        self.nlp_explainer = None
        self._initialize_engines()
        self._initialize_explainer()
    
    def _initialize_engines(self):
        """Initialize Hybrid Custom search engine"""
        logger.info("Initializing Hybrid Custom search engine...")
        
        try:
            self.hybrid_custom = HybridCustomSearchEngine(
                docs_root_dir=DOCS_ROOT_DIR, 
                tfidf_weight=0.4, 
                bm25_weight=0.6,
                mongo_connection_string=MONGODB_CONNECTION_STRING
            )
            logger.info("Hybrid Custom Search initialized (TF-IDF + BM25 + Adaptive Feedback)")
        except Exception as e:
            logger.error(f"Hybrid Custom Search failed: {e}")
    
    def _initialize_explainer(self):
        """Initialize NLP explainer for error explanations"""
        logger.info("Initializing NLP Error Explainer...")
        
        try:
            # Use lightweight model for faster initialization
            self.nlp_explainer = get_explainer(model_name="t5-small")
            logger.info("NLP Explainer initialized (T5-small model)")
        except Exception as e:
            logger.warning(f"NLP Explainer initialization failed: {e}")
            logger.info("Explanations will use rule-based fallback")
    
    def get_engine(self, method):
        """Get search engine by method name"""
        # Always return hybrid for any method
        return self.hybrid_custom
    
    def get_explainer(self):
        """Get NLP explainer instance"""
        return self.nlp_explainer
    
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
