"""
Status Controller
Handles system status and health checks
"""
from api.services import search_service


def get_system_status():
    """
    Get overall system status
    
    Returns:
        dict: System status information
    """
    engines = search_service.get_all_engines()
    
    custom_tfidf_corrections = 0
    enhanced_custom_corrections = 0
    hybrid_custom_corrections = 0
    
    if engines['custom_tfidf']:
        try:
            custom_tfidf_corrections = len(engines['custom_tfidf'].feedback_documents)
        except:
            pass
    
    if engines['enhanced_custom']:
        try:
            enhanced_custom_corrections = len(engines['enhanced_custom'].feedback_documents)
        except:
            pass
    
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
            print(f"[WARN] Could not get feedback stats: {e}")
    
    healthy = search_service.is_healthy()
    
    methods_available = []
    if engines['custom_tfidf']:
        methods_available.append('CUSTOM_TFIDF')
    if engines['enhanced_custom']:
        methods_available.append('ENHANCED_CUSTOM')
    if engines['hybrid_custom']:
        methods_available.append('HYBRID_CUSTOM')
    
    model_status = f"{', '.join(methods_available)}" if methods_available else "No methods loaded"
    
    return {
        'healthy': healthy,
        'model_status': model_status,
        'learned_corrections': custom_tfidf_corrections + enhanced_custom_corrections + hybrid_custom_corrections,
        'corrections_by_engine': {
            'custom_tfidf': custom_tfidf_corrections,
            'enhanced_custom': enhanced_custom_corrections,
            'hybrid_custom': hybrid_custom_corrections
        },
        'feedback_loop': feedback_stats
    }


def get_engines_comparison():
    """
    Get detailed comparison of search engines
    
    Returns:
        dict: Comparison data for all engines
    """
    engines = search_service.get_all_engines()
    
    comparison_data = {
        'engines': [
            {
                'id': 'CUSTOM_TFIDF',
                'name': 'Custom TF-IDF',
                'technology': 'Custom TF-IDF + Cosine Similarity',
                'description': 'Fast and simple custom search using TF-IDF vectorization and cosine similarity - 100% custom implementation',
                'strengths': [
                    '100% custom implementation - no blackbox libraries',
                    'Fast and lightweight',
                    'Easy to understand and debug',
                    'Works well for keyword matching',
                    'Complete mathematical transparency'
                ],
                'weaknesses': [
                    'No clustering or fuzzy matching',
                    'Limited to exact keyword matches',
                    'No handling of typos',
                    'Basic ranking algorithm'
                ],
                'best_for': [
                    'Understanding ML algorithms',
                    'Keyword-based matching',
                    'Lightweight deployments',
                    'Educational projects',
                    'Quick prototyping'
                ],
                'algorithm': 'Custom TF-IDF with cosine similarity (implemented from scratch)',
                'indexing': 'In-memory TF-IDF matrix with custom similarity search',
                'feedback_system': 'Custom in-memory feedback vectorizer',
                'performance': 'Fast (< 40ms typical)',
                'available': engines['custom_tfidf'] is not None,
                'custom_ml_features': [
                    'TF-IDF Vectorization',
                    'Cosine Similarity',
                    'Custom Tokenization',
                    'N-gram Generation (1-2)',
                    'Stop Words Filtering'
                ]
            },
            {
                'id': 'ENHANCED_CUSTOM',
                'name': 'Enhanced Custom (All Custom ML)',
                'technology': 'Custom TF-IDF + K-Means + Edit Distance + Custom Chunking',
                'description': 'Advanced search using ALL custom ML implementations: TF-IDF, Cosine Similarity, K-Means Clustering, Levenshtein Distance, and Custom Text Chunking',
                'strengths': [
                    '100% custom implementation - no blackbox libraries',
                    'Document clustering with K-Means',
                    'Fuzzy matching handles typos with edit distance',
                    'Intelligent text chunking for long documents',
                    'Multi-algorithm approach for robust matching',
                    'Complete mathematical transparency'
                ],
                'weaknesses': [
                    'More computationally intensive',
                    'Longer initialization time',
                    'Higher memory usage',
                    'No pre-trained semantic embeddings'
                ],
                'best_for': [
                    'Advanced error classification',
                    'Handling typos and variations',
                    'Long documentation search',
                    'Demonstrating multiple ML algorithms',
                    'Research and education'
                ],
                'algorithm': 'Fusion of Custom TF-IDF, K-Means, Edit Distance, and Chunking algorithms',
                'indexing': 'Multi-level indexing with clustering and chunk-based search',
                'feedback_system': 'Custom in-memory feedback with all algorithms',
                'performance': 'Moderate (< 100ms typical)',
                'available': engines['enhanced_custom'] is not None,
                'custom_ml_features': [
                    'TF-IDF Vectorization',
                    'Cosine Similarity',
                    'K-Means Clustering',
                    'Levenshtein Edit Distance',
                    'Fuzzy String Matching',
                    'Custom Text Chunking',
                    'N-gram Generation (1-3)'
                ]
            },
            {
                'id': 'HYBRID_CUSTOM',
                'name': 'Hybrid Custom (TF-IDF + BM25)',
                'technology': 'Custom TF-IDF + BM25 Ranking + Adaptive Feedback Loop',
                'description': 'State-of-the-art hybrid search combining TF-IDF and BM25 probabilistic ranking with reinforcement learning feedback loop - 100% custom implementation',
                'strengths': [
                    '100% custom implementation - no blackbox libraries',
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
                'performance': 'Fast (< 50ms typical, < 5ms for learned patterns)',
                'available': engines['hybrid_custom'] is not None,
                'custom_ml_features': [
                    'TF-IDF Vectorization',
                    'BM25 Ranking (Okapi BM25)',
                    'Score Normalization',
                    'Weighted Score Fusion',
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
                    'Persists learning to disk',
                    'Provides transparency into adjustments'
                ]
            }
        ],
        'recommendation': 'HYBRID_CUSTOM for production use - best accuracy with adaptive learning. CUSTOM_TFIDF for simplicity and speed. ENHANCED_CUSTOM for educational purposes.',
        'all_custom': True,
        'no_blackbox': True
    }
    
    return comparison_data
