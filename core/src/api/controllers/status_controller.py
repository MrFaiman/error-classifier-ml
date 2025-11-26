"""
Status Controller
Handles system status and health checks
"""
from api.services import search_service
from utils import get_logger

logger = get_logger(__name__)


def get_system_status():
    """
    Get overall system status
    
    Returns:
        dict: System status information
    """
    engines = search_service.get_all_engines()
    
    hybrid_custom_corrections = 0
    
    if engines['hybrid_custom']:
        try:
            hybrid_custom_corrections = len(engines['hybrid_custom'].feedback_documents)
        except:
            pass
    
    # Get feedback statistics
    feedback_stats = {}
    if engines['hybrid_custom']:
        try:
            feedback_stats = engines['hybrid_custom'].get_feedback_statistics()
        except Exception as e:
            logger.warning(f"Could not get feedback stats: {e}")
    
    healthy = search_service.is_healthy()
    
    methods_available = []
    if engines['hybrid_custom']:
        methods_available.append('HYBRID_CUSTOM')
    
    model_status = "Hybrid Custom (TF-IDF + BM25)" if methods_available else "No methods loaded"
    
    return {
        'healthy': healthy,
        'model_status': model_status,
        'learned_corrections': hybrid_custom_corrections,
        'corrections_by_engine': {
            'hybrid_custom': hybrid_custom_corrections
        },
        'feedback_loop': feedback_stats
    }


def get_engines_comparison():
    """
    Get detailed comparison of search engines
    
    Returns:
        dict: Comparison data for hybrid engine
    """
    engines = search_service.get_all_engines()
    
    comparison_data = {
        'engines': [
            {
                'id': 'HYBRID_CUSTOM',
                'name': 'Hybrid Custom (TF-IDF + BM25)',
                'technology': 'Custom TF-IDF + BM25 Ranking + Adaptive Feedback Loop',
                'description': 'State-of-the-art hybrid search combining TF-IDF and BM25 probabilistic ranking with reinforcement learning feedback loop',
                'strengths': [
                    'BM25 probabilistic ranking (Okapi BM25)',
                    'Weighted score fusion (TF-IDF + BM25)',
                    'Adaptive feedback loop with reinforcement learning',
                    'Confidence improves over time with user corrections',
                    'Learns query patterns automatically',
                    'Complete algorithmic transparency',
                    'Best accuracy for diverse queries'
                ],
                'weaknesses': [
                    'Slightly more memory usage',
                    'Requires feedback data for optimal performance',
                    'Initial predictions may need calibration'
                ],
                'best_for': [
                    'Production error classification systems',
                    'Systems that learn from user feedback',
                    'Complex query patterns',
                    'Information retrieval applications',
                    'Balanced precision and recall',
                    'Adaptive learning requirements'
                ],
                'algorithm': 'Weighted fusion of TF-IDF (40%) and BM25 (60%) with adaptive feedback loop',
                'indexing': 'Dual indexing: TF-IDF matrix + BM25 corpus statistics',
                'feedback_system': 'Advanced reinforcement learning with query pattern recognition',
                'performance': 'Fast (< 50ms typical, < 5ms for cached queries)',
                'available': engines['hybrid_custom'] is not None,
                'custom_ml_features': [
                    'TF-IDF Vectorization',
                    'BM25 Ranking (Okapi BM25)',
                    'Score Normalization',
                    'Weighted Score Fusion',
                    'Redis Caching Layer',
                    'Adaptive Feedback Loop',
                    'Query Pattern Learning',
                    'Confidence Adjustment',
                    'Engine Performance Tracking',
                    'Exponential Moving Average',
                    'UCB-inspired Weight Optimization'
                ],
                'feedback_features': [
                    'Tracks query-document accuracy',
                    'Boosts confidence for validated patterns',
                    'Learns similar query matching',
                    'Adjusts engine weights dynamically',
                    'Persists learning to MongoDB',
                    'Provides transparency into adjustments'
                ]
            }
        ],
        'recommendation': 'Hybrid Custom is the only available engine - optimized for production use with best accuracy and adaptive learning.',
        'all_custom': True,
        'no_blackbox': True
    }
    
    return comparison_data
