"""
MongoDB Database Manager for Feedback System
Handles persistent storage of feedback data with MongoDB
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os


class MongoFeedbackDatabase:
    """
    MongoDB database for feedback loop storage
    
    Collections:
    - predictions: All predictions made by the system
    - corrections: User corrections/feedback
    - query_patterns: Learned query patterns
    - engine_stats: Per-engine performance metrics
    - document_stats: Per-document accuracy
    - query_doc_stats: Query-document pair statistics
    """
    
    def __init__(self, connection_string: str, database_name: str = 'error_classifier'):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection string
            database_name: Database name
        """
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        
        # Collections
        self.predictions_col = self.db['predictions']
        self.corrections_col = self.db['corrections']
        self.query_patterns_col = self.db['query_patterns']
        self.engine_stats_col = self.db['engine_stats']
        self.document_stats_col = self.db['document_stats']
        self.query_doc_stats_col = self.db['query_doc_stats']
        
        self._create_indexes()
    
    def _create_indexes(self):
        """Create indexes for performance"""
        # Predictions indexes
        self.predictions_col.create_index([('query_normalized', ASCENDING)])
        self.predictions_col.create_index([('predicted_doc', ASCENDING)])
        self.predictions_col.create_index([('engine', ASCENDING)])
        self.predictions_col.create_index([('timestamp', DESCENDING)])
        
        # Corrections indexes
        self.corrections_col.create_index([('is_correct', ASCENDING)])
        self.corrections_col.create_index([('engine', ASCENDING)])
        self.corrections_col.create_index([('query_normalized', ASCENDING)])
        
        # Query patterns indexes
        self.query_patterns_col.create_index([('query_normalized', ASCENDING)], unique=True)
        self.query_patterns_col.create_index([('best_doc', ASCENDING)])
        
        # Engine stats indexes
        self.engine_stats_col.create_index([('engine', ASCENDING)], unique=True)
        
        # Document stats indexes
        self.document_stats_col.create_index([('doc_path', ASCENDING)], unique=True)
        self.document_stats_col.create_index([('accuracy', DESCENDING)])
        
        # Query-doc stats indexes
        self.query_doc_stats_col.create_index([
            ('query_normalized', ASCENDING),
            ('doc_path', ASCENDING)
        ], unique=True)
        self.query_doc_stats_col.create_index([('success_rate', DESCENDING)])
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for pattern matching"""
        return ' '.join(query.lower().split())
    
    def record_prediction(self, query: str, predicted_doc: str, 
                         confidence: float, engine: str,
                         adjusted_confidence: Optional[float] = None) -> str:
        """
        Record a prediction made by the system
        
        Returns:
            prediction_id (MongoDB ObjectId as string)
        """
        query_normalized = self._normalize_query(query)
        
        doc = {
            'query': query,
            'query_normalized': query_normalized,
            'predicted_doc': predicted_doc,
            'confidence': float(confidence),
            'adjusted_confidence': float(adjusted_confidence) if adjusted_confidence else None,
            'engine': engine,
            'timestamp': datetime.utcnow().isoformat(),
            'created_at': datetime.utcnow()
        }
        
        result = self.predictions_col.insert_one(doc)
        return str(result.inserted_id)
    
    def record_correction(self, query: str, predicted_doc: str, actual_doc: str,
                         is_correct: bool, original_confidence: float,
                         engine: str, prediction_id: Optional[str] = None):
        """Record user correction/feedback"""
        query_normalized = self._normalize_query(query)
        
        # Insert correction
        correction_doc = {
            'prediction_id': prediction_id,
            'query': query,
            'query_normalized': query_normalized,
            'predicted_doc': predicted_doc,
            'actual_doc': actual_doc,
            'is_correct': is_correct,
            'original_confidence': float(original_confidence),
            'engine': engine,
            'timestamp': datetime.utcnow().isoformat(),
            'created_at': datetime.utcnow()
        }
        
        self.corrections_col.insert_one(correction_doc)
        
        # Update aggregations
        self._update_query_doc_stats(query_normalized, actual_doc, is_correct)
        self._update_engine_stats(engine, is_correct)
        self._update_document_stats(actual_doc, True)  # Shown
        if is_correct:
            self._update_document_stats(actual_doc, True, is_correct=True)
        self._update_query_patterns(query_normalized, actual_doc)
    
    def _update_query_doc_stats(self, query_normalized: str, doc_path: str, is_correct: bool):
        """Update query-document pair statistics"""
        stats = self.query_doc_stats_col.find_one({
            'query_normalized': query_normalized,
            'doc_path': doc_path
        })
        
        if stats:
            correct_count = stats['correct_count'] + (1 if is_correct else 0)
            incorrect_count = stats['incorrect_count'] + (0 if is_correct else 1)
            total_count = stats['total_count'] + 1
            success_rate = correct_count / total_count if total_count > 0 else 0.5
            
            self.query_doc_stats_col.update_one(
                {'_id': stats['_id']},
                {
                    '$set': {
                        'correct_count': correct_count,
                        'incorrect_count': incorrect_count,
                        'total_count': total_count,
                        'success_rate': success_rate,
                        'last_updated': datetime.utcnow()
                    }
                }
            )
        else:
            self.query_doc_stats_col.insert_one({
                'query_normalized': query_normalized,
                'doc_path': doc_path,
                'correct_count': 1 if is_correct else 0,
                'incorrect_count': 0 if is_correct else 1,
                'total_count': 1,
                'success_rate': 1.0 if is_correct else 0.0,
                'last_updated': datetime.utcnow()
            })
    
    def _update_engine_stats(self, engine: str, is_correct: bool):
        """Update engine performance statistics"""
        stats = self.engine_stats_col.find_one({'engine': engine})
        
        if stats:
            total = stats['total_predictions'] + 1
            correct = stats['correct_predictions'] + (1 if is_correct else 0)
            incorrect = stats['incorrect_predictions'] + (0 if is_correct else 1)
            accuracy = correct / total if total > 0 else 0.5
            
            self.engine_stats_col.update_one(
                {'_id': stats['_id']},
                {
                    '$set': {
                        'total_predictions': total,
                        'correct_predictions': correct,
                        'incorrect_predictions': incorrect,
                        'accuracy': accuracy,
                        'last_updated': datetime.utcnow()
                    }
                }
            )
        else:
            self.engine_stats_col.insert_one({
                'engine': engine,
                'total_predictions': 1,
                'correct_predictions': 1 if is_correct else 0,
                'incorrect_predictions': 0 if is_correct else 1,
                'accuracy': 1.0 if is_correct else 0.0,
                'weight': 1.0,
                'last_updated': datetime.utcnow()
            })
    
    def _update_document_stats(self, doc_path: str, shown: bool, is_correct: bool = False):
        """Update document accuracy statistics"""
        stats = self.document_stats_col.find_one({'doc_path': doc_path})
        
        if stats:
            times_shown = stats['times_shown'] + (1 if shown else 0)
            times_correct = stats['times_correct'] + (1 if is_correct else 0)
            accuracy = times_correct / times_shown if times_shown > 0 else 0.5
            
            self.document_stats_col.update_one(
                {'_id': stats['_id']},
                {
                    '$set': {
                        'times_shown': times_shown,
                        'times_correct': times_correct,
                        'accuracy': accuracy,
                        'last_updated': datetime.utcnow()
                    }
                }
            )
        else:
            self.document_stats_col.insert_one({
                'doc_path': doc_path,
                'times_shown': 1 if shown else 0,
                'times_correct': 1 if is_correct else 0,
                'accuracy': 1.0 if is_correct else 0.5,
                'last_updated': datetime.utcnow()
            })
    
    def _update_query_patterns(self, query_normalized: str, doc_path: str):
        """Update learned query patterns"""
        pattern = self.query_patterns_col.find_one({'query_normalized': query_normalized})
        
        if pattern:
            total = pattern['total_count'] + 1
            best_count = pattern.get('best_doc_count', 0)
            
            # Update if this doc is the best match
            if pattern.get('best_doc') == doc_path:
                best_count += 1
            elif best_count == 0 or doc_path != pattern.get('best_doc'):
                # Check if this should be the new best
                doc_count = list(self.corrections_col.find({
                    'query_normalized': query_normalized,
                    'actual_doc': doc_path
                }))
                if len(doc_count) > best_count:
                    best_count = len(doc_count)
                    self.query_patterns_col.update_one(
                        {'_id': pattern['_id']},
                        {
                            '$set': {
                                'best_doc': doc_path,
                                'best_doc_count': best_count,
                                'total_count': total,
                                'last_updated': datetime.utcnow()
                            }
                        }
                    )
                    return
            
            self.query_patterns_col.update_one(
                {'_id': pattern['_id']},
                {
                    '$set': {
                        'best_doc_count': best_count,
                        'total_count': total,
                        'last_updated': datetime.utcnow()
                    }
                }
            )
        else:
            self.query_patterns_col.insert_one({
                'query_normalized': query_normalized,
                'best_doc': doc_path,
                'best_doc_count': 1,
                'total_count': 1,
                'avg_confidence': 0.0,
                'success_rate': 0.5,
                'last_updated': datetime.utcnow()
            })
    
    def get_query_doc_stats(self, query: str, doc_path: str) -> Optional[Dict]:
        """Get statistics for a query-document pair"""
        query_normalized = self._normalize_query(query)
        return self.query_doc_stats_col.find_one({
            'query_normalized': query_normalized,
            'doc_path': doc_path
        })
    
    def get_document_stats(self, doc_path: str) -> Optional[Dict]:
        """Get accuracy statistics for a document"""
        return self.document_stats_col.find_one({'doc_path': doc_path})
    
    def get_engine_stats(self, engine: str) -> Optional[Dict]:
        """Get performance statistics for an engine"""
        return self.engine_stats_col.find_one({'engine': engine})
    
    def get_all_engine_stats(self) -> List[Dict]:
        """Get statistics for all engines"""
        return list(self.engine_stats_col.find())
    
    def get_best_document_for_query(self, query: str) -> Optional[Tuple[str, int]]:
        """Get the best document for a query pattern"""
        query_normalized = self._normalize_query(query)
        pattern = self.query_patterns_col.find_one({'query_normalized': query_normalized})
        
        if pattern and pattern.get('best_doc'):
            return pattern['best_doc'], pattern['best_doc_count']
        
        return None
    
    def get_statistics(self) -> Dict:
        """Get overall feedback statistics"""
        total_corrections = self.corrections_col.count_documents({})
        correct_corrections = self.corrections_col.count_documents({'is_correct': True})
        
        overall_accuracy = (correct_corrections / total_corrections) if total_corrections > 0 else 0.0
        
        unique_queries = len(self.query_patterns_col.distinct('query_normalized'))
        unique_docs = len(self.document_stats_col.distinct('doc_path'))
        
        return {
            'total_feedback': total_corrections,
            'correct_feedback': correct_corrections,
            'incorrect_feedback': total_corrections - correct_corrections,
            'overall_accuracy': overall_accuracy,
            'unique_queries': unique_queries,
            'unique_documents': unique_docs
        }
    
    def get_top_documents(self, limit: int = 10) -> List[Dict]:
        """Get top performing documents"""
        return list(
            self.document_stats_col.find()
            .sort([('accuracy', DESCENDING), ('times_shown', DESCENDING)])
            .limit(limit)
        )
    
    def get_recent_corrections(self, limit: int = 100) -> List[Dict]:
        """Get recent corrections"""
        return list(
            self.corrections_col.find()
            .sort([('created_at', DESCENDING)])
            .limit(limit)
        )
    
    def export_to_json(self) -> Dict:
        """Export all data to JSON format (for backup/migration)"""
        def convert_doc(doc):
            """Convert MongoDB document to JSON-serializable dict"""
            if doc is None:
                return None
            doc_copy = dict(doc)
            doc_copy['_id'] = str(doc_copy['_id'])
            return doc_copy
        
        return {
            'predictions': [convert_doc(doc) for doc in self.predictions_col.find()],
            'corrections': [convert_doc(doc) for doc in self.corrections_col.find()],
            'query_patterns': [convert_doc(doc) for doc in self.query_patterns_col.find()],
            'engine_stats': [convert_doc(doc) for doc in self.engine_stats_col.find()],
            'document_stats': [convert_doc(doc) for doc in self.document_stats_col.find()],
            'query_doc_stats': [convert_doc(doc) for doc in self.query_doc_stats_col.find()]
        }
    
    def cleanup_old_predictions(self, days: int = 30):
        """Clean up old prediction records"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = self.predictions_col.delete_many({
            'created_at': {'$lt': cutoff_date}
        })
        
        return result.deleted_count
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
