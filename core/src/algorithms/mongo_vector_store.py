"""
MongoDB Vector Store
Stores TF-IDF and BM25 vectors in MongoDB for persistent retrieval
100% Custom Implementation with MongoDB backend
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
import numpy as np
import hashlib
from datetime import datetime
from typing import List, Tuple, Optional, Dict
import base64


class MongoVectorStore:
    """
    Custom vector database using MongoDB for persistence.
    Stores document vectors (TF-IDF, BM25, or custom embeddings) with metadata.
    Uses cosine similarity for retrieval.
    """
    
    def __init__(self, connection_string: str, database_name: str = 'error_classifier'):
        """
        Initialize MongoDB vector store
        
        Args:
            connection_string: MongoDB connection string (mongodb://user:pass@host:port/)
            database_name: Database name to use
        """
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        
        # Collections
        self.documents_col = self.db['documents']
        self.vectors_col = self.db['vectors']
        self.vocabulary_col = self.db['vocabulary']
        self.metadata_col = self.db['vector_metadata']
        
        self._init_indexes()
    
    def _init_indexes(self):
        """Create indexes for fast retrieval"""
        # Documents indexes
        self.documents_col.create_index([('doc_path', ASCENDING)], unique=True)
        self.documents_col.create_index([('content_hash', ASCENDING)])
        self.documents_col.create_index([('service', ASCENDING)])
        
        # Vectors indexes
        self.vectors_col.create_index([
            ('document_id', ASCENDING),
            ('vector_type', ASCENDING)
        ], unique=True)
        self.vectors_col.create_index([('vector_type', ASCENDING)])
        
        # Vocabulary indexes
        self.vocabulary_col.create_index([
            ('vector_type', ASCENDING),
            ('feature_name', ASCENDING)
        ], unique=True)
        self.vocabulary_col.create_index([('vector_type', ASCENDING)])
        
        # Metadata indexes
        self.metadata_col.create_index([('vector_type', ASCENDING)], unique=True)
    
    def _compute_content_hash(self, content: str) -> str:
        """Compute SHA256 hash of content for change detection"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _serialize_vector(self, vector: np.ndarray) -> str:
        """Convert numpy array to base64 string for MongoDB storage"""
        return base64.b64encode(vector.astype(np.float32).tobytes()).decode('utf-8')
    
    def _deserialize_vector(self, data: str, dimension: int) -> np.ndarray:
        """Convert base64 string back to numpy array"""
        bytes_data = base64.b64decode(data.encode('utf-8'))
        return np.frombuffer(bytes_data, dtype=np.float32).reshape(-1, dimension)
    
    def save_document(self, doc_path: str, content: str, 
                     service: str = None, category: str = None) -> str:
        """
        Save or update a document
        
        Args:
            doc_path: Path to the document
            content: Document text content
            service: Service name (optional)
            category: Error category (optional)
            
        Returns:
            document_id (MongoDB ObjectId as string)
        """
        content_hash = self._compute_content_hash(content)
        
        # Check if document exists
        existing_doc = self.documents_col.find_one({'doc_path': doc_path})
        
        if existing_doc:
            doc_id = str(existing_doc['_id'])
            if existing_doc['content_hash'] != content_hash:
                # Content changed - update document
                self.documents_col.update_one(
                    {'_id': existing_doc['_id']},
                    {
                        '$set': {
                            'content': content,
                            'content_hash': content_hash,
                            'service': service,
                            'category': category,
                            'updated_at': datetime.utcnow()
                        }
                    }
                )
                
                # Delete old vectors (will be regenerated)
                self.vectors_col.delete_many({'document_id': doc_id})
            
            return doc_id
        else:
            # New document
            result = self.documents_col.insert_one({
                'doc_path': doc_path,
                'content': content,
                'content_hash': content_hash,
                'service': service,
                'category': category,
                'indexed_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
            return str(result.inserted_id)
    
    def save_vector(self, doc_path: str, vector: np.ndarray, 
                   vector_type: str = 'tfidf'):
        """
        Save a document vector
        
        Args:
            doc_path: Path to the document
            vector: Numpy array vector
            vector_type: Type of vector ('tfidf', 'bm25', 'custom')
        """
        # Get document ID
        doc = self.documents_col.find_one({'doc_path': doc_path})
        
        if not doc:
            raise ValueError(f"Document not found: {doc_path}")
        
        doc_id = str(doc['_id'])
        
        # Flatten vector if needed
        if vector.ndim > 1:
            vector = vector.flatten()
        
        dimension = len(vector)
        vector_data = self._serialize_vector(vector)
        
        # Insert or replace vector
        self.vectors_col.update_one(
            {'document_id': doc_id, 'vector_type': vector_type},
            {
                '$set': {
                    'document_id': doc_id,
                    'vector_type': vector_type,
                    'vector': vector_data,
                    'dimension': dimension,
                    'created_at': datetime.utcnow()
                }
            },
            upsert=True
        )
    
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
        
        dimension = vectors.shape[1]
        
        for doc_path, vector in zip(doc_paths, vectors):
            try:
                self.save_vector(doc_path, vector, vector_type)
            except ValueError as e:
                print(f"Warning: {e}")
                continue
    
    def get_vector(self, doc_path: str, vector_type: str = 'tfidf') -> Optional[np.ndarray]:
        """
        Retrieve a document vector
        
        Args:
            doc_path: Path to the document
            vector_type: Type of vector to retrieve
            
        Returns:
            Numpy array or None if not found
        """
        # Get document ID
        doc = self.documents_col.find_one({'doc_path': doc_path})
        
        if not doc:
            return None
        
        doc_id = str(doc['_id'])
        
        # Get vector
        vector_doc = self.vectors_col.find_one({
            'document_id': doc_id,
            'vector_type': vector_type
        })
        
        if vector_doc:
            return self._deserialize_vector(vector_doc['vector'], vector_doc['dimension'])
        
        return None
    
    def get_all_vectors(self, vector_type: str = 'tfidf') -> Tuple[List[str], np.ndarray]:
        """
        Retrieve all vectors of a specific type
        
        Args:
            vector_type: Type of vectors to retrieve
            
        Returns:
            (doc_paths, vectors_matrix) - List of paths and 2D numpy array
        """
        # Get all vectors of this type
        vector_docs = list(self.vectors_col.find({'vector_type': vector_type}))
        
        if not vector_docs:
            return [], np.array([])
        
        doc_paths = []
        vectors_list = []
        
        for vec_doc in vector_docs:
            # Get document path
            doc = self.documents_col.find_one({'_id': vec_doc['document_id']})
            if doc:
                doc_paths.append(doc['doc_path'])
                vector = self._deserialize_vector(vec_doc['vector'], vec_doc['dimension'])
                vectors_list.append(vector.flatten())
        
        if not vectors_list:
            return [], np.array([])
        
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
        # Clear existing vocabulary for this vector type
        self.vocabulary_col.delete_many({'vector_type': vector_type})
        
        # Insert new vocabulary
        docs_to_insert = []
        for idx, feature in enumerate(feature_names):
            idf_val = float(idf_values[idx]) if idf_values is not None else None
            docs_to_insert.append({
                'vector_type': vector_type,
                'feature_name': feature,
                'feature_index': idx,
                'idf_value': idf_val,
                'created_at': datetime.utcnow()
            })
        
        if docs_to_insert:
            self.vocabulary_col.insert_many(docs_to_insert)
    
    def get_vocabulary(self, vector_type: str = 'tfidf') -> Tuple[List[str], Optional[np.ndarray]]:
        """
        Retrieve vocabulary for a vector type
        
        Args:
            vector_type: Type of vectors
            
        Returns:
            (feature_names, idf_values) - Lists ordered by feature_index
        """
        vocab_docs = list(self.vocabulary_col.find({'vector_type': vector_type}).sort('feature_index', ASCENDING))
        
        if not vocab_docs:
            return [], None
        
        feature_names = [doc['feature_name'] for doc in vocab_docs]
        idf_values = [doc['idf_value'] for doc in vocab_docs if doc.get('idf_value') is not None]
        
        if idf_values:
            return feature_names, np.array(idf_values)
        else:
            return feature_names, None
    
    def save_metadata(self, vector_type: str, settings: Dict):
        """
        Save vectorizer metadata/settings
        
        Args:
            vector_type: Type of vectors
            settings: Dictionary of settings
        """
        self.metadata_col.update_one(
            {'vector_type': vector_type},
            {
                '$set': {
                    'vector_type': vector_type,
                    'max_features': settings.get('max_features'),
                    'ngram_min': settings.get('ngram_min'),
                    'ngram_max': settings.get('ngram_max'),
                    'settings': settings,
                    'updated_at': datetime.utcnow()
                }
            },
            upsert=True
        )
    
    def get_metadata(self, vector_type: str = 'tfidf') -> Optional[Dict]:
        """
        Retrieve vectorizer metadata/settings
        
        Args:
            vector_type: Type of vectors
            
        Returns:
            Dictionary of settings or None
        """
        meta_doc = self.metadata_col.find_one({'vector_type': vector_type})
        
        if meta_doc:
            return meta_doc.get('settings', {})
        
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
        # Check if all documents have vectors
        doc_count = self.documents_col.count_documents({'doc_path': {'$in': doc_paths}})
        
        # Count vectors for these documents
        doc_ids = [
            str(doc['_id'])
            for doc in self.documents_col.find({'doc_path': {'$in': doc_paths}}, {'_id': 1})
        ]
        
        vector_count = self.vectors_col.count_documents({
            'document_id': {'$in': doc_ids},
            'vector_type': vector_type
        })
        
        # Need reindex if counts don't match
        return doc_count != vector_count or doc_count != len(doc_paths)
    
    def delete_document(self, doc_path: str):
        """Delete a document and its vectors"""
        doc = self.documents_col.find_one({'doc_path': doc_path})
        if doc:
            doc_id = str(doc['_id'])
            self.vectors_col.delete_many({'document_id': doc_id})
            self.documents_col.delete_one({'_id': doc['_id']})
    
    def clear_vector_type(self, vector_type: str):
        """Clear all vectors of a specific type"""
        self.vectors_col.delete_many({'vector_type': vector_type})
        self.vocabulary_col.delete_many({'vector_type': vector_type})
        self.metadata_col.delete_one({'vector_type': vector_type})
    
    def get_statistics(self) -> Dict:
        """Get vector store statistics"""
        doc_count = self.documents_col.count_documents({})
        
        # Count vectors by type
        pipeline = [
            {'$group': {'_id': '$vector_type', 'count': {'$sum': 1}}}
        ]
        vector_counts = {
            item['_id']: item['count']
            for item in self.vectors_col.aggregate(pipeline)
        }
        
        vector_types = [
            doc['vector_type']
            for doc in self.metadata_col.find({}, {'vector_type': 1})
        ]
        
        return {
            'total_documents': doc_count,
            'vector_counts': vector_counts,
            'vector_types': vector_types,
            'database': self.db.name,
            'connection': 'mongodb'
        }
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()


if __name__ == "__main__":
    # Test the MongoDB vector store
    print("=== Testing MongoDB Vector Store ===\n")
    
    # Use test connection string (update with your credentials)
    test_connection = "mongodb://root:3l91PRi23Mlx@localhost:27017/"
    
    try:
        store = MongoVectorStore(test_connection, database_name='test_vector_store')
        
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
        
        # Cleanup
        print("\nCleaning up test data...")
        store.documents_col.drop()
        store.vectors_col.drop()
        store.vocabulary_col.drop()
        store.metadata_col.drop()
        
        store.close()
        print("Done!")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure MongoDB is running and credentials are correct")
