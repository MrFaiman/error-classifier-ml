"""
SQLite Database Manager for Feedback System
Handles persistent storage of feedback data with SQL queries
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import os


class FeedbackDatabase:
    """
    SQLite database for feedback loop storage
    
    Tables:
    - predictions: All predictions made by the system
    - corrections: User corrections/feedback
    - query_patterns: Learned query patterns
    - engine_stats: Per-engine performance metrics
    - document_stats: Per-document accuracy
    """
    
    def __init__(self, db_path: str):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._create_tables()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _create_tables(self):
        """Create database schema if it doesn't exist"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Predictions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    query_normalized TEXT NOT NULL,
                    predicted_doc TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    adjusted_confidence REAL,
                    engine TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_query_normalized (query_normalized),
                    INDEX idx_predicted_doc (predicted_doc),
                    INDEX idx_engine (engine),
                    INDEX idx_timestamp (timestamp)
                )
            """)
            
            # Corrections/Feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS corrections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id INTEGER,
                    query TEXT NOT NULL,
                    query_normalized TEXT NOT NULL,
                    predicted_doc TEXT NOT NULL,
                    actual_doc TEXT NOT NULL,
                    is_correct INTEGER NOT NULL,
                    original_confidence REAL NOT NULL,
                    engine TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prediction_id) REFERENCES predictions(id),
                    INDEX idx_is_correct (is_correct),
                    INDEX idx_engine_corrections (engine),
                    INDEX idx_query_normalized_corrections (query_normalized)
                )
            """)
            
            # Query patterns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_normalized TEXT UNIQUE NOT NULL,
                    best_doc TEXT,
                    best_doc_count INTEGER DEFAULT 0,
                    total_count INTEGER DEFAULT 0,
                    avg_confidence REAL DEFAULT 0.0,
                    success_rate REAL DEFAULT 0.5,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_best_doc (best_doc)
                )
            """)
            
            # Engine statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS engine_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    engine TEXT UNIQUE NOT NULL,
                    total_predictions INTEGER DEFAULT 0,
                    correct_predictions INTEGER DEFAULT 0,
                    incorrect_predictions INTEGER DEFAULT 0,
                    accuracy REAL DEFAULT 0.5,
                    weight REAL DEFAULT 1.0,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Document statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_path TEXT UNIQUE NOT NULL,
                    times_shown INTEGER DEFAULT 0,
                    times_correct INTEGER DEFAULT 0,
                    accuracy REAL DEFAULT 0.5,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_accuracy (accuracy)
                )
            """)
            
            # Query-Document pair statistics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_doc_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_normalized TEXT NOT NULL,
                    doc_path TEXT NOT NULL,
                    correct_count INTEGER DEFAULT 0,
                    incorrect_count INTEGER DEFAULT 0,
                    total_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.5,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(query_normalized, doc_path),
                    INDEX idx_success_rate (success_rate)
                )
            """)
    
    def record_prediction(self, query: str, query_normalized: str, 
                         predicted_doc: str, confidence: float,
                         adjusted_confidence: float, engine: str) -> int:
        """
        Record a prediction made by the system
        
        Returns:
            prediction_id for linking to corrections
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO predictions 
                (query, query_normalized, predicted_doc, confidence, adjusted_confidence, engine, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (query, query_normalized, predicted_doc, confidence, 
                  adjusted_confidence, engine, datetime.now().isoformat()))
            
            return cursor.lastrowid
    
    def record_correction(self, query: str, query_normalized: str,
                         predicted_doc: str, actual_doc: str,
                         is_correct: bool, original_confidence: float,
                         engine: str, prediction_id: Optional[int] = None) -> int:
        """Record user feedback/correction"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO corrections
                (prediction_id, query, query_normalized, predicted_doc, actual_doc, 
                 is_correct, original_confidence, engine, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (prediction_id, query, query_normalized, predicted_doc, actual_doc,
                  int(is_correct), original_confidence, engine, datetime.now().isoformat()))
            
            correction_id = cursor.lastrowid
            
            # Update aggregated statistics
            self._update_query_doc_stats(conn, query_normalized, predicted_doc, is_correct)
            self._update_engine_stats(conn, engine, is_correct)
            self._update_document_stats(conn, predicted_doc, is_correct)
            self._update_query_patterns(conn, query_normalized, actual_doc if is_correct else None)
            
            return correction_id
    
    def _update_query_doc_stats(self, conn, query_normalized: str, doc_path: str, is_correct: bool):
        """Update query-document pair statistics"""
        cursor = conn.cursor()
        
        # Get or create record
        cursor.execute("""
            INSERT INTO query_doc_stats (query_normalized, doc_path, correct_count, incorrect_count, total_count)
            VALUES (?, ?, 0, 0, 0)
            ON CONFLICT(query_normalized, doc_path) DO NOTHING
        """, (query_normalized, doc_path))
        
        # Update counts
        if is_correct:
            cursor.execute("""
                UPDATE query_doc_stats
                SET correct_count = correct_count + 1,
                    total_count = total_count + 1,
                    success_rate = CAST(correct_count + 1 AS REAL) / (total_count + 1),
                    last_updated = CURRENT_TIMESTAMP
                WHERE query_normalized = ? AND doc_path = ?
            """, (query_normalized, doc_path))
        else:
            cursor.execute("""
                UPDATE query_doc_stats
                SET incorrect_count = incorrect_count + 1,
                    total_count = total_count + 1,
                    success_rate = CAST(correct_count AS REAL) / (total_count + 1),
                    last_updated = CURRENT_TIMESTAMP
                WHERE query_normalized = ? AND doc_path = ?
            """, (query_normalized, doc_path))
    
    def _update_engine_stats(self, conn, engine: str, is_correct: bool):
        """Update engine performance statistics"""
        cursor = conn.cursor()
        
        # Get or create record
        cursor.execute("""
            INSERT INTO engine_stats (engine, total_predictions, correct_predictions, incorrect_predictions)
            VALUES (?, 0, 0, 0)
            ON CONFLICT(engine) DO NOTHING
        """, (engine,))
        
        # Update counts
        if is_correct:
            cursor.execute("""
                UPDATE engine_stats
                SET total_predictions = total_predictions + 1,
                    correct_predictions = correct_predictions + 1,
                    accuracy = CAST(correct_predictions + 1 AS REAL) / (total_predictions + 1),
                    last_updated = CURRENT_TIMESTAMP
                WHERE engine = ?
            """, (engine,))
        else:
            cursor.execute("""
                UPDATE engine_stats
                SET total_predictions = total_predictions + 1,
                    incorrect_predictions = incorrect_predictions + 1,
                    accuracy = CAST(correct_predictions AS REAL) / (total_predictions + 1),
                    last_updated = CURRENT_TIMESTAMP
                WHERE engine = ?
            """, (engine,))
    
    def _update_document_stats(self, conn, doc_path: str, is_correct: bool):
        """Update document accuracy statistics"""
        cursor = conn.cursor()
        
        # Get or create record
        cursor.execute("""
            INSERT INTO document_stats (doc_path, times_shown, times_correct)
            VALUES (?, 0, 0)
            ON CONFLICT(doc_path) DO NOTHING
        """, (doc_path,))
        
        # Update counts
        if is_correct:
            cursor.execute("""
                UPDATE document_stats
                SET times_shown = times_shown + 1,
                    times_correct = times_correct + 1,
                    accuracy = CAST(times_correct + 1 AS REAL) / (times_shown + 1),
                    last_updated = CURRENT_TIMESTAMP
                WHERE doc_path = ?
            """, (doc_path,))
        else:
            cursor.execute("""
                UPDATE document_stats
                SET times_shown = times_shown + 1,
                    accuracy = CAST(times_correct AS REAL) / (times_shown + 1),
                    last_updated = CURRENT_TIMESTAMP
                WHERE doc_path = ?
            """, (doc_path,))
    
    def _update_query_patterns(self, conn, query_normalized: str, correct_doc: Optional[str]):
        """Update query pattern learning"""
        cursor = conn.cursor()
        
        # Get or create record
        cursor.execute("""
            INSERT INTO query_patterns (query_normalized, total_count)
            VALUES (?, 0)
            ON CONFLICT(query_normalized) DO NOTHING
        """, (query_normalized,))
        
        # Update pattern
        if correct_doc:
            cursor.execute("""
                UPDATE query_patterns
                SET total_count = total_count + 1,
                    best_doc = CASE 
                        WHEN best_doc = ? THEN ?
                        WHEN best_doc IS NULL THEN ?
                        ELSE best_doc
                    END,
                    best_doc_count = CASE
                        WHEN best_doc = ? THEN best_doc_count + 1
                        WHEN best_doc IS NULL THEN 1
                        ELSE best_doc_count
                    END,
                    last_updated = CURRENT_TIMESTAMP
                WHERE query_normalized = ?
            """, (correct_doc, correct_doc, correct_doc, correct_doc, query_normalized))
    
    def get_query_doc_stats(self, query_normalized: str, doc_path: str) -> Optional[Dict]:
        """Get statistics for a specific query-document pair"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM query_doc_stats
                WHERE query_normalized = ? AND doc_path = ?
            """, (query_normalized, doc_path))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_document_stats(self, doc_path: str) -> Optional[Dict]:
        """Get statistics for a document"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM document_stats
                WHERE doc_path = ?
            """, (doc_path,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_engine_stats(self, engine: str) -> Optional[Dict]:
        """Get statistics for an engine"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM engine_stats
                WHERE engine = ?
            """, (engine,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_engine_stats(self) -> List[Dict]:
        """Get statistics for all engines"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM engine_stats ORDER BY accuracy DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_best_document_for_query(self, query_normalized: str) -> Optional[Tuple[str, float]]:
        """Get the best known document for a query"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT best_doc, best_doc_count, total_count
                FROM query_patterns
                WHERE query_normalized = ? AND best_doc IS NOT NULL AND best_doc_count >= 2
            """, (query_normalized,))
            
            row = cursor.fetchone()
            if row:
                confidence = 95.0 + min(5.0, row['best_doc_count'])
                return row['best_doc'], confidence
            
            return None
    
    def get_top_documents(self, limit: int = 10) -> List[Dict]:
        """Get top performing documents"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT doc_path, times_shown, times_correct, accuracy
                FROM document_stats
                WHERE times_shown >= 3
                ORDER BY accuracy DESC, times_shown DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict:
        """Get comprehensive feedback statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total feedback
            cursor.execute("SELECT COUNT(*) as total FROM corrections")
            total_feedback = cursor.fetchone()['total']
            
            # Correct predictions
            cursor.execute("SELECT COUNT(*) as correct FROM corrections WHERE is_correct = 1")
            correct_feedback = cursor.fetchone()['correct']
            
            # Unique queries
            cursor.execute("SELECT COUNT(DISTINCT query_normalized) as unique FROM corrections")
            unique_queries = cursor.fetchone()['unique']
            
            # Unique documents
            cursor.execute("SELECT COUNT(*) as unique FROM document_stats WHERE times_shown > 0")
            unique_documents = cursor.fetchone()['unique']
            
            # Engine stats
            engine_stats = self.get_all_engine_stats()
            
            # Top documents
            top_documents = self.get_top_documents(5)
            
            return {
                'total_feedback': total_feedback,
                'correct_predictions': correct_feedback,
                'overall_accuracy': correct_feedback / total_feedback if total_feedback > 0 else 0.0,
                'unique_queries': unique_queries,
                'unique_documents': unique_documents,
                'engine_stats': {stat['engine']: stat for stat in engine_stats},
                'top_documents': top_documents
            }
    
    def get_recent_corrections(self, limit: int = 100) -> List[Dict]:
        """Get recent corrections for analysis"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM corrections
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def export_to_json(self, filepath: str):
        """Export all feedback data to JSON (for backup/migration)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            data = {
                'predictions': [dict(row) for row in cursor.execute("SELECT * FROM predictions")],
                'corrections': [dict(row) for row in cursor.execute("SELECT * FROM corrections")],
                'query_patterns': [dict(row) for row in cursor.execute("SELECT * FROM query_patterns")],
                'engine_stats': [dict(row) for row in cursor.execute("SELECT * FROM engine_stats")],
                'document_stats': [dict(row) for row in cursor.execute("SELECT * FROM document_stats")],
                'query_doc_stats': [dict(row) for row in cursor.execute("SELECT * FROM query_doc_stats")],
            }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def cleanup_old_predictions(self, days: int = 90):
        """Clean up old prediction records (keep corrections)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM predictions
                WHERE created_at < datetime('now', ? || ' days')
                AND id NOT IN (SELECT prediction_id FROM corrections WHERE prediction_id IS NOT NULL)
            """, (f'-{days}',))
            
            deleted = cursor.rowcount
            return deleted


if __name__ == "__main__":
    # Test database
    import tempfile
    
    print("Testing Feedback Database")
    print("=" * 70)
    
    # Create temp database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db = FeedbackDatabase(db_path)
    print(f"✓ Database created: {db_path}\n")
    
    # Test predictions
    print("1. Recording predictions...")
    pred_id1 = db.record_prediction(
        "negative value error",
        "negative value error",
        "services/logitrack/NEGATIVE_VALUE.md",
        75.0, 82.5, "HYBRID_CUSTOM"
    )
    print(f"  ✓ Prediction recorded: ID {pred_id1}")
    
    # Test corrections
    print("\n2. Recording corrections...")
    db.record_correction(
        "negative value error",
        "negative value error",
        "services/logitrack/NEGATIVE_VALUE.md",
        "services/logitrack/NEGATIVE_VALUE.md",
        True, 75.0, "HYBRID_CUSTOM", pred_id1
    )
    print("  ✓ Correct prediction recorded")
    
    db.record_correction(
        "schema error",
        "schema error",
        "services/meteo-il/SCHEMA_VALIDATION.md",
        "services/skyguard/SCHEMA_VALIDATION.md",
        False, 80.0, "ENHANCED_CUSTOM"
    )
    print("  ✓ Incorrect prediction recorded")
    
    # Test queries
    print("\n3. Querying statistics...")
    stats = db.get_statistics()
    print(f"  Total feedback: {stats['total_feedback']}")
    print(f"  Overall accuracy: {stats['overall_accuracy']:.2%}")
    
    engine_stats = db.get_all_engine_stats()
    print(f"\n4. Engine statistics:")
    for stat in engine_stats:
        print(f"  {stat['engine']}: {stat['accuracy']:.2%} ({stat['correct_predictions']}/{stat['total_predictions']})")
    
    # Test export
    print("\n5. Testing JSON export...")
    json_path = db_path.replace('.db', '.json')
    db.export_to_json(json_path)
    print(f"  ✓ Exported to {json_path}")
    
    print("\n✅ All database tests completed!")
    print(f"\nDatabase file: {db_path}")
    print(f"JSON export: {json_path}")
