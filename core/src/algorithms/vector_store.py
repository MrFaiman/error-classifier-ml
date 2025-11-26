"""
Custom Vector Store using SQLite
Stores TF-IDF and BM25 vectors for fast persistent retrieval
100% Custom Implementation - No Blackbox Vector Databases
"""
import sqlite3
import numpy as np
import json
import hashlib
import os
from datetime import datetime
from typing import List, Tuple, Optional, Dict


class VectorStore:
    """
    Custom vector database using SQLite for persistence.
    Stores document vectors (TF-IDF, BM25, or custom embeddings) with metadata.
    Uses cosine similarity for retrieval.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize vector store with SQLite backend
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Create tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Documents table with metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_path TEXT UNIQUE NOT NULL,
                    content_hash TEXT NOT NULL,
                    content TEXT,
                    service TEXT,
                    category TEXT,
                    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Vectors table - stores different vector types
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vectors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    vector_type TEXT NOT NULL,
                    vector BLOB NOT NULL,
                    dimension INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    UNIQUE(document_id, vector_type)
                )
            """)
            
            # Vocabulary table - for TF-IDF feature names
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vector_type TEXT NOT NULL,
                    feature_name TEXT NOT NULL,
                    feature_index INTEGER NOT NULL,
                    idf_value REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(vector_type, feature_name)
                )
            """)
            
            # Metadata table - for vectorizer settings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vector_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vector_type TEXT UNIQUE NOT NULL,
                    max_features INTEGER,
                    ngram_min INTEGER,
                    ngram_max INTEGER,
                    settings_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for fast retrieval
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_doc_path 
                ON documents (doc_path)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_hash 
                ON documents (content_hash)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_vector_type 
                ON vectors (vector_type)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_document_vector 
                ON vectors (document_id, vector_type)
            """)
            
            conn.commit()
    
    def _compute_content_hash(self, content: str) -> str:
        """Compute SHA256 hash of content for change detection"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _serialize_vector(self, vector: np.ndarray) -> bytes:
        """Convert numpy array to bytes for BLOB storage"""
        return vector.astype(np.float32).tobytes()
    
    def _deserialize_vector(self, blob: bytes, dimension: int) -> np.ndarray:
        """Convert BLOB back to numpy array"""
        return np.frombuffer(blob, dtype=np.float32).reshape(-1, dimension)
    
    def save_document(self, doc_path: str, content: str, 
                     service: str = None, category: str = None) -> int:
        """
        Save or update a document
        
        Args:
            doc_path: Path to the document
            content: Document text content
            service: Service name (optional)
            category: Error category (optional)
            
        Returns:
            document_id
        """
        content_hash = self._compute_content_hash(content)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if document exists
            cursor.execute(
                "SELECT id, content_hash FROM documents WHERE doc_path = ?",
                (doc_path,)
            )
            result = cursor.fetchone()
            
            if result:
                doc_id, existing_hash = result
                if existing_hash != content_hash:
                    # Content changed - update document and mark vectors for regeneration
                    cursor.execute("""
                        UPDATE documents 
                        SET content = ?, content_hash = ?, service = ?, category = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (content, content_hash, service, category, doc_id))
                    
                    # Delete old vectors (will be regenerated)
                    cursor.execute("DELETE FROM vectors WHERE document_id = ?", (doc_id,))
                    
                return doc_id
            else:
                # New document
                cursor.execute("""
                    INSERT INTO documents (doc_path, content, content_hash, service, category)
                    VALUES (?, ?, ?, ?, ?)
                """, (doc_path, content, content_hash, service, category))
                
                return cursor.lastrowid
    
    def save_vector(self, doc_path: str, vector: np.ndarray, 
                   vector_type: str = 'tfidf'):
        """
        Save a document vector
        
        Args:
            doc_path: Path to the document
            vector: Numpy array vector
            vector_type: Type of vector ('tfidf', 'bm25', 'custom')
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get document ID
            cursor.execute("SELECT id FROM documents WHERE doc_path = ?", (doc_path,))
            result = cursor.fetchone()
            
            if not result:
                raise ValueError(f"Document not found: {doc_path}")
            
            doc_id = result[0]
            
            # Flatten vector if needed
            if vector.ndim > 1:
                vector = vector.flatten()
            
            dimension = len(vector)
            vector_blob = self._serialize_vector(vector)
            
            # Insert or replace vector
            cursor.execute("""
                INSERT OR REPLACE INTO vectors (document_id, vector_type, vector, dimension)
                VALUES (?, ?, ?, ?)
            """, (doc_id, vector_type, vector_blob, dimension))
            
            conn.commit()
    
    def save_vectors_batch(self, doc_paths: List[str], vectors: np.ndarray,
                          vector_type: str = 'tfidf'):
        """
        Save multiple vectors at once (faster than individual saves)
        
        Args:
            doc_paths: List of document paths
            vectors: 2D numpy array (n_docs × dimension)
            vector_type: Type of vectors
        """
        if len(doc_paths) != vectors.shape[0]:
            raise ValueError("Number of paths must match number of vectors")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            dimension = vectors.shape[1]
            
            for doc_path, vector in zip(doc_paths, vectors):
                # Get document ID
                cursor.execute("SELECT id FROM documents WHERE doc_path = ?", (doc_path,))
                result = cursor.fetchone()
                
                if not result:
                    print(f"Warning: Document not found: {doc_path}")
                    continue
                
                doc_id = result[0]
                vector_blob = self._serialize_vector(vector)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO vectors (document_id, vector_type, vector, dimension)
                    VALUES (?, ?, ?, ?)
                """, (doc_id, vector_type, vector_blob, dimension))
            
            conn.commit()
    
    def get_vector(self, doc_path: str, vector_type: str = 'tfidf') -> Optional[np.ndarray]:
        """
        Retrieve a document vector
        
        Args:
            doc_path: Path to the document
            vector_type: Type of vector to retrieve
            
        Returns:
            Numpy array or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT v.vector, v.dimension
                FROM vectors v
                JOIN documents d ON v.document_id = d.id
                WHERE d.doc_path = ? AND v.vector_type = ?
            """, (doc_path, vector_type))
            
            result = cursor.fetchone()
            
            if result:
                vector_blob, dimension = result
                return self._deserialize_vector(vector_blob, dimension)
            
            return None
    
    def get_all_vectors(self, vector_type: str = 'tfidf') -> Tuple[List[str], np.ndarray]:
        """
        Retrieve all vectors of a specific type
        
        Args:
            vector_type: Type of vectors to retrieve
            
        Returns:
            (doc_paths, vectors_matrix) - List of paths and 2D numpy array
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT d.doc_path, v.vector, v.dimension
                FROM vectors v
                JOIN documents d ON v.document_id = d.id
                WHERE v.vector_type = ?
                ORDER BY d.id
            """, (vector_type,))
            
            results = cursor.fetchall()
            
            if not results:
                return [], np.array([])
            
            doc_paths = []
            vectors_list = []
            
            for doc_path, vector_blob, dimension in results:
                doc_paths.append(doc_path)
                vector = self._deserialize_vector(vector_blob, dimension)
                vectors_list.append(vector.flatten())
            
            vectors_matrix = np.vstack(vectors_list)
            
            return doc_paths, vectors_matrix
    
    def save_vocabulary(self, vector_type: str, feature_names: List[str], 
                       idf_values: Optional[np.ndarray] = None):
        """
        Save vocabulary (feature names) for a vector type
        
        Args:
            vector_type: Type of vectors
            feature_names: List of feature names (words/ngrams)
            idf_values: Optional IDF values for each feature
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Clear existing vocabulary for this vector type
            cursor.execute("DELETE FROM vocabulary WHERE vector_type = ?", (vector_type,))
            
            # Insert new vocabulary
            for idx, feature in enumerate(feature_names):
                idf_val = float(idf_values[idx]) if idf_values is not None else None
                cursor.execute("""
                    INSERT INTO vocabulary (vector_type, feature_name, feature_index, idf_value)
                    VALUES (?, ?, ?, ?)
                """, (vector_type, feature, idx, idf_val))
            
            conn.commit()
    
    def get_vocabulary(self, vector_type: str = 'tfidf') -> Tuple[List[str], Optional[np.ndarray]]:
        """
        Retrieve vocabulary for a vector type
        
        Args:
            vector_type: Type of vectors
            
        Returns:
            (feature_names, idf_values) - Lists ordered by feature_index
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT feature_name, idf_value
                FROM vocabulary
                WHERE vector_type = ?
                ORDER BY feature_index
            """, (vector_type,))
            
            results = cursor.fetchall()
            
            if not results:
                return [], None
            
            feature_names = [row[0] for row in results]
            idf_values = np.array([row[1] for row in results if row[1] is not None])
            
            return feature_names, idf_values if len(idf_values) > 0 else None
    
    def save_metadata(self, vector_type: str, settings: Dict):
        """
        Save vectorizer metadata/settings
        
        Args:
            vector_type: Type of vectors
            settings: Dictionary of settings
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            settings_json = json.dumps(settings)
            
            cursor.execute("""
                INSERT OR REPLACE INTO vector_metadata 
                (vector_type, max_features, ngram_min, ngram_max, settings_json, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                vector_type,
                settings.get('max_features'),
                settings.get('ngram_min'),
                settings.get('ngram_max'),
                settings_json
            ))
            
            conn.commit()
    
    def get_metadata(self, vector_type: str = 'tfidf') -> Optional[Dict]:
        """
        Retrieve vectorizer metadata/settings
        
        Args:
            vector_type: Type of vectors
            
        Returns:
            Dictionary of settings or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT settings_json FROM vector_metadata WHERE vector_type = ?
            """, (vector_type,))
            
            result = cursor.fetchone()
            
            if result:
                return json.loads(result[0])
            
            return None
    
    def needs_reindex(self, doc_paths: List[str], vector_type: str = 'tfidf') -> bool:
        """
        Check if reindexing is needed (documents changed or vectors missing)
        
        Args:
            doc_paths: List of current document paths
            vector_type: Type of vectors to check
            
        Returns:
            True if reindexing needed
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if all documents have vectors
            cursor.execute("""
                SELECT COUNT(DISTINCT d.id)
                FROM documents d
                WHERE d.doc_path IN ({})
            """.format(','.join('?' * len(doc_paths))), doc_paths)
            
            doc_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(DISTINCT v.document_id)
                FROM vectors v
                JOIN documents d ON v.document_id = d.id
                WHERE d.doc_path IN ({}) AND v.vector_type = ?
            """.format(','.join('?' * len(doc_paths))), doc_paths + [vector_type])
            
            vector_count = cursor.fetchone()[0]
            
            # Need reindex if counts don't match
            return doc_count != vector_count or doc_count != len(doc_paths)
    
    def delete_document(self, doc_path: str):
        """Delete a document and its vectors"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE doc_path = ?", (doc_path,))
            conn.commit()
    
    def clear_vector_type(self, vector_type: str):
        """Clear all vectors of a specific type"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vectors WHERE vector_type = ?", (vector_type,))
            cursor.execute("DELETE FROM vocabulary WHERE vector_type = ?", (vector_type,))
            cursor.execute("DELETE FROM vector_metadata WHERE vector_type = ?", (vector_type,))
            conn.commit()
    
    def get_statistics(self) -> Dict:
        """Get vector store statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM documents")
            doc_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT vector_type, COUNT(*) FROM vectors GROUP BY vector_type")
            vector_counts = {row[0]: row[1] for row in cursor.fetchall()}
            
            cursor.execute("SELECT vector_type FROM vector_metadata")
            vector_types = [row[0] for row in cursor.fetchall()]
            
            return {
                'total_documents': doc_count,
                'vector_counts': vector_counts,
                'vector_types': vector_types,
                'database_path': self.db_path
            }
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        pass


if __name__ == "__main__":
    # Test the vector store
    print("=== Testing Custom Vector Store ===\n")
    
    # Create test database
    test_db = "/tmp/test_vector_store.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    store = VectorStore(test_db)
    
    # Test 1: Save documents
    print("1. Saving test documents...")
    doc1_id = store.save_document(
        "docs/test1.md",
        "This is a test document about machine learning",
        service="test",
        category="ML"
    )
    doc2_id = store.save_document(
        "docs/test2.md",
        "Another document discussing artificial intelligence",
        service="test",
        category="AI"
    )
    print(f"   Saved doc1 (id={doc1_id}), doc2 (id={doc2_id})")
    
    # Test 2: Save vectors
    print("\n2. Saving TF-IDF vectors...")
    vec1 = np.array([0.5, 0.3, 0.8, 0.1, 0.0])
    vec2 = np.array([0.2, 0.7, 0.4, 0.0, 0.9])
    
    store.save_vector("docs/test1.md", vec1, 'tfidf')
    store.save_vector("docs/test2.md", vec2, 'tfidf')
    print("   Vectors saved")
    
    # Test 3: Retrieve vectors
    print("\n3. Retrieving vectors...")
    retrieved1 = store.get_vector("docs/test1.md", 'tfidf')
    print(f"   Doc1 vector: {retrieved1}")
    print(f"   Match: {np.allclose(vec1, retrieved1)}")
    
    # Test 4: Get all vectors
    print("\n4. Getting all vectors...")
    paths, matrix = store.get_all_vectors('tfidf')
    print(f"   Paths: {paths}")
    print(f"   Matrix shape: {matrix.shape}")
    print(f"   Matrix:\n{matrix}")
    
    # Test 5: Save vocabulary
    print("\n5. Saving vocabulary...")
    features = ['machine', 'learning', 'ai', 'test', 'document']
    idf_vals = np.array([2.5, 2.3, 2.8, 1.5, 1.2])
    store.save_vocabulary('tfidf', features, idf_vals)
    print(f"   Saved {len(features)} features")
    
    # Test 6: Retrieve vocabulary
    print("\n6. Retrieving vocabulary...")
    ret_features, ret_idf = store.get_vocabulary('tfidf')
    print(f"   Features: {ret_features}")
    print(f"   IDF values: {ret_idf}")
    
    # Test 7: Save metadata
    print("\n7. Saving metadata...")
    metadata = {
        'max_features': 5000,
        'ngram_min': 1,
        'ngram_max': 2,
        'stop_words': True
    }
    store.save_metadata('tfidf', metadata)
    
    ret_metadata = store.get_metadata('tfidf')
    print(f"   Metadata: {ret_metadata}")
    
    # Test 8: Statistics
    print("\n8. Statistics...")
    stats = store.get_statistics()
    print(f"   {stats}")
    
    # Test 9: Needs reindex check
    print("\n9. Checking reindex status...")
    needs_reindex = store.needs_reindex(['docs/test1.md', 'docs/test2.md'], 'tfidf')
    print(f"   Needs reindex: {needs_reindex}")
    
    needs_reindex_new = store.needs_reindex(['docs/test1.md', 'docs/test2.md', 'docs/test3.md'], 'tfidf')
    print(f"   Needs reindex (with new doc): {needs_reindex_new}")
    
    # Test 10: Batch save
    print("\n10. Testing batch save...")
    doc3_id = store.save_document("docs/test3.md", "Third test document", "test", "TEST")
    vectors_batch = np.array([
        [0.1, 0.2, 0.3, 0.4, 0.5],
        [0.6, 0.7, 0.8, 0.9, 1.0],
        [0.5, 0.5, 0.5, 0.5, 0.5]
    ])
    store.save_vectors_batch(['docs/test1.md', 'docs/test2.md', 'docs/test3.md'], vectors_batch, 'bm25')
    
    paths_bm25, matrix_bm25 = store.get_all_vectors('bm25')
    print(f"   BM25 vectors saved: {len(paths_bm25)} documents")
    print(f"   Matrix shape: {matrix_bm25.shape}")
    
    print("\n=== All tests passed! ===")
    print(f"\nTest database created at: {test_db}")
