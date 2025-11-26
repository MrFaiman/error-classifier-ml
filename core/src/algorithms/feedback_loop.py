"""
Feedback Loop System for Adaptive Learning
Implements reinforcement learning to improve search confidence over time
"""
import numpy as np
import json
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from collections import defaultdict
from .mongo_feedback_database import MongoFeedbackDatabase


class FeedbackLoop:
    """
    Adaptive learning system that improves search confidence through user feedback
    
    Features:
    1. Tracks correct/incorrect predictions per query-document pair
    2. Adjusts confidence scores based on historical accuracy
    3. Updates search engine weights dynamically
    4. Learns query patterns and common mistakes
    5. Provides confidence boost for validated results
    
    Uses concepts from:
    - Multi-armed bandit (UCB algorithm)
    - Bayesian updating
    - Exponential moving averages
    """
    
    def __init__(self, learning_rate=0.1, confidence_boost=5.0, confidence_penalty=10.0, 
                 mongo_connection=None):
        """
        Initialize feedback loop
        
        Args:
            learning_rate: How quickly to adapt (0-1, default 0.1)
            confidence_boost: Points to add for correct predictions
            confidence_penalty: Points to subtract for incorrect predictions
            mongo_connection: MongoDB connection string
        """
        self.learning_rate = learning_rate
        self.confidence_boost = confidence_boost
        self.confidence_penalty = confidence_penalty
        
        # Initialize database (MongoDB only)
        self.db = None
        self.use_database = False
        
        if mongo_connection:
            try:
                self.db = MongoFeedbackDatabase(mongo_connection)
                self.use_database = True
                print(f"[OK] Feedback database using MongoDB")
            except Exception as e:
                print(f"[WARNING] MongoDB connection failed: {e}")
                self.db = None
        
        # In-memory cache for backward compatibility and fast access
        # Track query -> document accuracy
        self.query_doc_stats = defaultdict(lambda: {
            'correct': 0,
            'incorrect': 0,
            'total': 0,
            'success_rate': 0.5  # Start with neutral prior
        })
        
        # Track document popularity and accuracy
        self.doc_stats = defaultdict(lambda: {
            'times_shown': 0,
            'times_correct': 0,
            'accuracy': 0.5
        })
        
        # Track query patterns
        self.query_patterns = defaultdict(lambda: {
            'count': 0,
            'avg_confidence': 0.0,
            'best_doc': None,
            'best_doc_count': 0
        })
        
        # Track engine performance
        self.engine_stats = defaultdict(lambda: {
            'predictions': 0,
            'correct': 0,
            'incorrect': 0,
            'accuracy': 0.5,
            'weight': 1.0  # Dynamic weight for ensemble
        })
        
        # Store feedback history (in-memory only for compatibility)
        self.feedback_history = []
        
        # Load existing data from database if available
        if self.use_database:
            self._sync_from_database()
        
    def _normalize_query(self, query: str) -> str:
        """Normalize query for pattern matching"""
        return ' '.join(query.lower().split())
    
    def _sync_from_database(self):
        """Sync in-memory cache from database"""
        if not self.use_database:
            return
        
        # Load engine stats
        engine_stats_list = self.db.get_all_engine_stats()
        for stat in engine_stats_list:
            self.engine_stats[stat['engine']] = {
                'predictions': stat['total_predictions'],
                'correct': stat['correct_predictions'],
                'incorrect': stat['incorrect_predictions'],
                'accuracy': stat['accuracy'],
                'weight': stat['weight']
            }
        
        # Load recent corrections for in-memory cache
        recent = self.db.get_recent_corrections(limit=1000)
        for correction in recent:
            self.feedback_history.append({
                'timestamp': correction['timestamp'],
                'query': correction['query'],
                'predicted_doc': correction['predicted_doc'],
                'actual_doc': correction['actual_doc'],
                'is_correct': bool(correction['is_correct']),
                'original_confidence': correction['original_confidence'],
                'engine': correction['engine']
            })
    
    def _compute_query_similarity(self, query1: str, query2: str) -> float:
        """Compute simple Jaccard similarity between queries"""
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def record_prediction(self, query: str, predicted_doc: str, 
                         confidence: float, engine: str = 'unknown'):
        """
        Record a prediction made by the system
        
        Args:
            query: The query text
            predicted_doc: Document path predicted
            confidence: Original confidence score
            engine: Which search engine made the prediction
        """
        normalized_query = self._normalize_query(query)
        
        # Record to database if available
        if self.use_database:
            self.db.record_prediction(
                query, normalized_query, predicted_doc,
                confidence, confidence, engine
            )
        
        # Update in-memory cache
        key = f"{normalized_query}||{predicted_doc}"
        self.query_doc_stats[key]['total'] += 1
        self.doc_stats[predicted_doc]['times_shown'] += 1
        self.engine_stats[engine]['predictions'] += 1
        
        # Update query patterns
        pattern = self.query_patterns[normalized_query]
        pattern['count'] += 1
        pattern['avg_confidence'] = (
            (pattern['avg_confidence'] * (pattern['count'] - 1) + confidence) / 
            pattern['count']
        )

        
    def record_feedback(self, query: str, predicted_doc: str, 
                       actual_doc: str, original_confidence: float,
                       engine: str = 'unknown') -> Dict:
        """
        Record user feedback (correction or confirmation)
        
        Args:
            query: The query text
            predicted_doc: What the system predicted
            actual_doc: What the user says is correct
            original_confidence: The original confidence score
            engine: Which search engine made the prediction
            
        Returns:
            Dictionary with updated stats and recommendations
        """
        normalized_query = self._normalize_query(query)
        is_correct = (predicted_doc == actual_doc)
        
        # Record to database if available
        if self.use_database:
            self.db.record_correction(
                query, normalized_query, predicted_doc, actual_doc,
                is_correct, original_confidence, engine
            )
        
        # Update in-memory cache
        key = f"{normalized_query}||{predicted_doc}"
        stats = self.query_doc_stats[key]
        
        if is_correct:
            stats['correct'] += 1
            self.doc_stats[predicted_doc]['times_correct'] += 1
            self.engine_stats[engine]['correct'] += 1
        else:
            stats['incorrect'] += 1
            self.engine_stats[engine]['incorrect'] += 1
        
        # Update success rate using exponential moving average
        alpha = self.learning_rate
        new_success = 1.0 if is_correct else 0.0
        stats['success_rate'] = (
            alpha * new_success + (1 - alpha) * stats['success_rate']
        )
        
        # Update document accuracy
        doc_stat = self.doc_stats[predicted_doc]
        if doc_stat['times_shown'] > 0:
            doc_stat['accuracy'] = doc_stat['times_correct'] / doc_stat['times_shown']
        
        # Update engine accuracy
        engine_stat = self.engine_stats[engine]
        total = engine_stat['correct'] + engine_stat['incorrect']
        if total > 0:
            engine_stat['accuracy'] = engine_stat['correct'] / total
            
            # Update engine weight using UCB-like formula
            # Higher accuracy and more data = higher confidence
            exploration_bonus = np.sqrt(2 * np.log(total + 1) / (total + 1))
            engine_stat['weight'] = engine_stat['accuracy'] + exploration_bonus
        
        # Update query patterns
        if is_correct:
            pattern = self.query_patterns[normalized_query]
            if pattern['best_doc'] == actual_doc:
                pattern['best_doc_count'] += 1
            elif pattern['best_doc'] is None or pattern['best_doc_count'] == 0:
                pattern['best_doc'] = actual_doc
                pattern['best_doc_count'] = 1
        
        # Store in history
        feedback_entry = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'predicted_doc': predicted_doc,
            'actual_doc': actual_doc,
            'is_correct': is_correct,
            'original_confidence': original_confidence,
            'engine': engine,
            'success_rate': stats['success_rate']
        }
        self.feedback_history.append(feedback_entry)
        
        # Return updated stats
        return {
            'is_correct': is_correct,
            'success_rate': stats['success_rate'],
            'query_total_feedback': stats['total'],
            'doc_accuracy': doc_stat['accuracy'],
            'engine_accuracy': engine_stat['accuracy'],
            'engine_weight': engine_stat['weight']
        }
    
    def adjust_confidence(self, query: str, doc: str, 
                         original_confidence: float,
                         engine: str = 'unknown') -> float:
        """
        Adjust confidence score based on historical feedback
        
        Args:
            query: The query text
            doc: The document path
            original_confidence: Original confidence score
            engine: Search engine used
            
        Returns:
            Adjusted confidence score (0-100)
        """
        normalized_query = self._normalize_query(query)
        adjusted = original_confidence
        
        # Try database first for accurate stats
        if self.use_database:
            # Get query-doc stats from database
            qd_stats = self.db.get_query_doc_stats(normalized_query, doc)
            if qd_stats and qd_stats['total_count'] > 0:
                success_rate = qd_stats['success_rate']
                if success_rate > 0.7:
                    adjusted += self.confidence_boost * (success_rate - 0.5)
                elif success_rate < 0.3:
                    adjusted -= self.confidence_penalty * (0.5 - success_rate)
            
            # Get document stats from database
            doc_stats = self.db.get_document_stats(doc)
            if doc_stats and doc_stats['times_shown'] >= 3:
                adjusted += (doc_stats['accuracy'] - 0.5) * 5
            
            # Get engine stats from database
            eng_stats = self.db.get_engine_stats(engine)
            if eng_stats and eng_stats['total_predictions'] >= 5:
                adjusted *= (0.8 + 0.4 * eng_stats['accuracy'])
        else:
            # Fallback to in-memory cache
            key = f"{normalized_query}||{doc}"
            
            # Adjust based on query-document history
            if key in self.query_doc_stats:
                stats = self.query_doc_stats[key]
                if stats['total'] > 0:
                    success_rate = stats['success_rate']
                    
                    if success_rate > 0.7:
                        adjusted += self.confidence_boost * (success_rate - 0.5)
                    elif success_rate < 0.3:
                        adjusted -= self.confidence_penalty * (0.5 - success_rate)
            
            # Adjust based on document accuracy
            if doc in self.doc_stats:
                doc_accuracy = self.doc_stats[doc]['accuracy']
                if self.doc_stats[doc]['times_shown'] >= 3:
                    adjusted += (doc_accuracy - 0.5) * 5
            
            # Adjust based on engine performance
            if engine in self.engine_stats:
                engine_accuracy = self.engine_stats[engine]['accuracy']
                total_predictions = self.engine_stats[engine]['predictions']
                if total_predictions >= 5:
                    adjusted *= (0.8 + 0.4 * engine_accuracy)
        
        # Check for similar successful queries
        similar_boost = self._get_similar_query_boost(normalized_query, doc)
        adjusted += similar_boost
        
        # Clamp to valid range
        return max(0.0, min(100.0, adjusted))
    
    def _get_similar_query_boost(self, query: str, doc: str) -> float:
        """Get confidence boost from similar successful queries"""
        boost = 0.0
        max_similarity = 0.0
        
        for pattern_query, pattern_data in self.query_patterns.items():
            if pattern_data['best_doc'] == doc and pattern_data['best_doc_count'] >= 2:
                similarity = self._compute_query_similarity(query, pattern_query)
                if similarity > max_similarity:
                    max_similarity = similarity
        
        # Boost up to 5 points based on similarity
        if max_similarity > 0.5:
            boost = 5.0 * (max_similarity - 0.5) * 2
        
        return boost
    
    def get_engine_weights(self) -> Dict[str, float]:
        """
        Get recommended weights for each search engine
        
        Returns:
            Dictionary of engine -> weight
        """
        weights = {}
        total_weight = 0.0
        
        for engine, stats in self.engine_stats.items():
            if stats['predictions'] > 0:
                weights[engine] = stats['weight']
                total_weight += stats['weight']
        
        # Normalize weights to sum to 1.0
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        return weights
    
    def get_best_document_for_query(self, query: str) -> Optional[Tuple[str, float]]:
        """
        Get the best known document for a query based on feedback
        
        Args:
            query: The query text
            
        Returns:
            Tuple of (document_path, confidence) or None
        """
        normalized_query = self._normalize_query(query)
        
        # Try database first
        if self.use_database:
            result = self.db.get_best_document_for_query(normalized_query)
            if result:
                return result
        
        # Fallback to in-memory patterns
        # Check exact match in patterns
        if normalized_query in self.query_patterns:
            pattern = self.query_patterns[normalized_query]
            if pattern['best_doc'] and pattern['best_doc_count'] >= 2:
                confidence = 95.0 + min(5.0, pattern['best_doc_count'])
                return pattern['best_doc'], confidence
        
        # Check similar queries
        best_doc = None
        best_score = 0.0
        
        for pattern_query, pattern_data in self.query_patterns.items():
            if pattern_data['best_doc'] and pattern_data['best_doc_count'] >= 2:
                similarity = self._compute_query_similarity(query, pattern_query)
                score = similarity * pattern_data['best_doc_count']
                
                if score > best_score and similarity > 0.6:
                    best_score = score
                    best_doc = pattern_data['best_doc']
        
        if best_doc:
            confidence = 80.0 + min(15.0, best_score * 5)
            return best_doc, confidence
        
        return None
    
    def get_statistics(self) -> Dict:
        """Get comprehensive feedback statistics"""
        # Use database stats if available
        if self.use_database:
            return self.db.get_statistics()
        
        # Fallback to in-memory stats
        total_feedback = len(self.feedback_history)
        correct_feedback = sum(1 for f in self.feedback_history if f['is_correct'])
        
        return {
            'total_feedback': total_feedback,
            'correct_predictions': correct_feedback,
            'overall_accuracy': correct_feedback / total_feedback if total_feedback > 0 else 0.0,
            'unique_queries': len(self.query_patterns),
            'unique_documents': len(self.doc_stats),
            'engine_stats': dict(self.engine_stats),
            'top_documents': self._get_top_documents(5),
            'learning_rate': self.learning_rate,
            'using_database': False
        }
    
    def _get_top_documents(self, n: int = 5) -> List[Dict]:
        """Get top N most accurate documents"""
        docs = []
        for doc, stats in self.doc_stats.items():
            if stats['times_shown'] >= 3:  # Need enough data
                docs.append({
                    'document': doc,
                    'accuracy': stats['accuracy'],
                    'times_shown': stats['times_shown'],
                    'times_correct': stats['times_correct']
                })
        
        docs.sort(key=lambda x: (x['accuracy'], x['times_shown']), reverse=True)
        return docs[:n]
    
    def save_to_file(self, filepath: str):
        """Save feedback data to JSON file (export from database if available)"""
        if self.use_database:
            # Export from database
            self.db.export_to_json(filepath)
        else:
            # Save from in-memory data
            data = {
                'query_doc_stats': dict(self.query_doc_stats),
                'doc_stats': dict(self.doc_stats),
                'query_patterns': dict(self.query_patterns),
                'engine_stats': dict(self.engine_stats),
                'feedback_history': self.feedback_history[-1000:],  # Keep last 1000
                'config': {
                    'learning_rate': self.learning_rate,
                    'confidence_boost': self.confidence_boost,
                    'confidence_penalty': self.confidence_penalty
                }
            }
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
    
    def load_from_file(self, filepath: str):
        """Load feedback data from JSON file"""
        if not os.path.exists(filepath):
            return
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.query_doc_stats = defaultdict(lambda: {
            'correct': 0, 'incorrect': 0, 'total': 0, 'success_rate': 0.5
        }, data.get('query_doc_stats', {}))
        
        self.doc_stats = defaultdict(lambda: {
            'times_shown': 0, 'times_correct': 0, 'accuracy': 0.5
        }, data.get('doc_stats', {}))
        
        self.query_patterns = defaultdict(lambda: {
            'count': 0, 'avg_confidence': 0.0, 'best_doc': None, 'best_doc_count': 0
        }, data.get('query_patterns', {}))
        
        self.engine_stats = defaultdict(lambda: {
            'predictions': 0, 'correct': 0, 'incorrect': 0, 'accuracy': 0.5, 'weight': 1.0
        }, data.get('engine_stats', {}))
        
        self.feedback_history = data.get('feedback_history', [])
        
        config = data.get('config', {})
        self.learning_rate = config.get('learning_rate', self.learning_rate)
        self.confidence_boost = config.get('confidence_boost', self.confidence_boost)
        self.confidence_penalty = config.get('confidence_penalty', self.confidence_penalty)


if __name__ == "__main__":
    # Test feedback loop
    print("Testing Feedback Loop System")
    print("=" * 70)
    
    feedback = FeedbackLoop(learning_rate=0.15, confidence_boost=8.0)
    
    # Simulate some predictions and feedback
    print("\n1. Recording Predictions...")
    
    predictions = [
        ("negative value error", "services/logitrack/NEGATIVE_VALUE.md", 75.0, "CUSTOM_TFIDF"),
        ("negative value problem", "services/logitrack/NEGATIVE_VALUE.md", 78.0, "HYBRID_CUSTOM"),
        ("schema validation failed", "services/meteo-il/SCHEMA_VALIDATION.md", 82.0, "ENHANCED_CUSTOM"),
        ("negative value", "services/logitrack/NEGATIVE_VALUE.md", 80.0, "HYBRID_CUSTOM"),
    ]
    
    for query, doc, conf, engine in predictions:
        feedback.record_prediction(query, doc, conf, engine)
        print(f"  Recorded: '{query}' -> {doc} ({conf:.1f}%, {engine})")
    
    # Simulate user feedback
    print("\n2. Recording User Feedback...")
    
    feedbacks = [
        ("negative value error", "services/logitrack/NEGATIVE_VALUE.md", 
         "services/logitrack/NEGATIVE_VALUE.md", 75.0, "CUSTOM_TFIDF"),  # Correct
        ("negative value problem", "services/logitrack/NEGATIVE_VALUE.md",
         "services/logitrack/NEGATIVE_VALUE.md", 78.0, "HYBRID_CUSTOM"),  # Correct
        ("schema validation failed", "services/meteo-il/SCHEMA_VALIDATION.md",
         "services/skyguard/SCHEMA_VALIDATION.md", 82.0, "ENHANCED_CUSTOM"),  # Wrong doc!
        ("negative value", "services/logitrack/NEGATIVE_VALUE.md",
         "services/logitrack/NEGATIVE_VALUE.md", 80.0, "HYBRID_CUSTOM"),  # Correct
    ]
    
    for query, pred, actual, conf, engine in feedbacks:
        result = feedback.record_feedback(query, pred, actual, conf, engine)
        status = "✓ CORRECT" if result['is_correct'] else "✗ INCORRECT"
        print(f"  {status}: '{query}'")
        print(f"    Success rate: {result['success_rate']:.2%}")
        print(f"    Engine accuracy: {result['engine_accuracy']:.2%}")
    
    # Test confidence adjustment
    print("\n3. Testing Confidence Adjustment...")
    
    test_queries = [
        ("negative value error", "services/logitrack/NEGATIVE_VALUE.md", 75.0, "HYBRID_CUSTOM"),
        ("schema validation failed", "services/meteo-il/SCHEMA_VALIDATION.md", 82.0, "ENHANCED_CUSTOM"),
        ("new negative value issue", "services/logitrack/NEGATIVE_VALUE.md", 70.0, "CUSTOM_TFIDF"),
    ]
    
    for query, doc, original_conf, engine in test_queries:
        adjusted_conf = feedback.adjust_confidence(query, doc, original_conf, engine)
        delta = adjusted_conf - original_conf
        symbol = "↑" if delta > 0 else "↓" if delta < 0 else "="
        print(f"  '{query}'")
        print(f"    Original: {original_conf:.1f}% -> Adjusted: {adjusted_conf:.1f}% ({symbol}{abs(delta):.1f})")
    
    # Get best document for query
    print("\n4. Testing Best Document Lookup...")
    
    best = feedback.get_best_document_for_query("negative value issue")
    if best:
        doc, conf = best
        print(f"  Query: 'negative value issue'")
        print(f"  Best match: {doc}")
        print(f"  Confidence: {conf:.1f}%")
    
    # Get engine weights
    print("\n5. Engine Weights (for ensemble)...")
    weights = feedback.get_engine_weights()
    for engine, weight in weights.items():
        print(f"  {engine}: {weight:.3f}")
    
    # Get statistics
    print("\n6. Overall Statistics...")
    stats = feedback.get_statistics()
    print(f"  Total feedback: {stats['total_feedback']}")
    print(f"  Correct predictions: {stats['correct_predictions']}")
    print(f"  Overall accuracy: {stats['overall_accuracy']:.2%}")
    print(f"  Unique queries: {stats['unique_queries']}")
    print(f"  Unique documents: {stats['unique_documents']}")
    
    print("\n  Top documents:")
    for i, doc_stat in enumerate(stats['top_documents'], 1):
        print(f"    {i}. {doc_stat['document']}")
        print(f"       Accuracy: {doc_stat['accuracy']:.2%} ({doc_stat['times_correct']}/{doc_stat['times_shown']})")
    
    # Test save/load
    print("\n7. Testing Save/Load...")
    feedback.save_to_file("/tmp/feedback_test.json")
    print("  ✓ Saved to /tmp/feedback_test.json")
    
    feedback2 = FeedbackLoop()
    feedback2.load_from_file("/tmp/feedback_test.json")
    print(f"  ✓ Loaded: {len(feedback2.feedback_history)} history entries")
    
    print("\n✅ All feedback loop tests completed!")
