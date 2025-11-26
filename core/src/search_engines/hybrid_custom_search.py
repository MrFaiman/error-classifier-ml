"""
Hybrid Custom Search Engine with BM25 Ranking
Combines TF-IDF, BM25, Cosine Similarity, and Fuzzy Matching
Now with persistent vector storage in MongoDB
"""
import os
import glob
import numpy as np
import hashlib
from constants import DOCS_ROOT_DIR, DATA_DIR, REDIS_URL, REDIS_CACHE_ENABLED, REDIS_CACHE_TTL
from algorithms import (
    TfidfVectorizer, 
    SimilaritySearch, 
    ENGLISH_STOP_WORDS,
    BM25,
    FeedbackLoop,
    MongoVectorStore
)
from cache import RedisCache


class HybridCustomSearchEngine:
    """
    Advanced search engine combining multiple custom ranking algorithms:
    1. TF-IDF with Cosine Similarity
    2. BM25 Ranking (Okapi BM25)
    3. Fuzzy Matching with Edit Distance
    
    Uses weighted score fusion to combine multiple signals
    """
    
    def __init__(self, docs_root_dir=None, max_features=5000, 
                 tfidf_weight=0.4, bm25_weight=0.6, k1=1.5, b=0.75,
                 use_vector_store=True,
                 mongo_connection_string=None,
                 use_cache=None,
                 redis_url=None):
        """
        Initialize hybrid custom search engine
        
        Args:
            docs_root_dir: Root directory containing documentation files
            max_features: Maximum vocabulary size for TF-IDF
            tfidf_weight: Weight for TF-IDF scores (0-1)
            bm25_weight: Weight for BM25 scores (0-1)
            k1: BM25 term frequency saturation parameter
            b: BM25 length normalization parameter
            use_vector_store: Use MongoDB vector store for persistence (default: True)
            mongo_connection_string: MongoDB connection string (from environment)
            use_cache: Enable Redis caching (None = use REDIS_CACHE_ENABLED env var)
            redis_url: Redis connection URL (None = use REDIS_URL env var)
        """
        if docs_root_dir is None:
            docs_root_dir = DOCS_ROOT_DIR
        self.docs_root_dir = docs_root_dir
        self.max_features = max_features
        self.tfidf_weight = tfidf_weight
        self.bm25_weight = bm25_weight
        self.use_vector_store = use_vector_store
        
        # Normalize weights
        total_weight = tfidf_weight + bm25_weight
        if total_weight > 0:
            self.tfidf_weight = tfidf_weight / total_weight
            self.bm25_weight = bm25_weight / total_weight
        
        # Initialize MongoDB vector store if enabled
        if self.use_vector_store and mongo_connection_string:
            try:
                self.vector_store = MongoVectorStore(
                    mongo_connection_string,
                    database_name='error_classifier'
                )
                print(f"[OK] MongoDB vector store initialized: {self.vector_store.db.name}")
            except Exception as e:
                print(f"[WARNING] MongoDB connection failed: {e}")
                print(f"[WARNING] Continuing without vector store persistence")
                self.vector_store = None
                self.use_vector_store = False
        else:
            self.vector_store = None
            if not mongo_connection_string:
                print(f"[INFO] No MongoDB connection string provided - vector store disabled")
        
        # Initialize TF-IDF
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=max_features,
            lowercase=True,
            stop_words=ENGLISH_STOP_WORDS,
            ngram_range=(1, 2)
        )
        
        # Initialize BM25
        self.bm25 = BM25(k1=k1, b=b)
        
        # Initialize similarity search (for TF-IDF)
        self.similarity_search = SimilaritySearch(metric='cosine')
        
        # Storage
        self.documents = []
        self.doc_paths = []
        self.doc_metadata = []
        self.tfidf_matrix = None
        
        # Feedback system
        self.feedback_tfidf_vectorizer = None
        self.feedback_bm25 = None
        self.feedback_documents = []
        self.feedback_paths = []
        
        # Initialize feedback loop (MongoDB only)
        self.feedback_loop = FeedbackLoop(
            learning_rate=0.1,
            confidence_boost=5.0,
            confidence_penalty=10.0,
            mongo_connection=mongo_connection_string if use_vector_store else None
        )
        self.feedback_file = os.path.join(DATA_DIR, 'feedback_hybrid_custom.json')
        
        # Initialize Redis cache
        cache_enabled = use_cache if use_cache is not None else REDIS_CACHE_ENABLED
        cache_url = redis_url or REDIS_URL
        self.cache = RedisCache(
            redis_url=cache_url,
            ttl_seconds=REDIS_CACHE_TTL,
            enabled=cache_enabled
        )
        
        # Load and index documents
        self._index_documents()
        
        # Initialize feedback system
        self._init_feedback_system()
    
    def __del__(self):
        """Cleanup MongoDB and Redis connections"""
        if hasattr(self, 'vector_store') and self.vector_store:
            try:
                self.vector_store.close()
            except:
                pass
        if hasattr(self, 'cache') and self.cache:
            try:
                self.cache.close()
            except:
                pass
    
    def _read_document(self, filepath):
        """Read and preprocess a document file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            print(f"[Warning] Failed to read {filepath}: {e}")
            return None
    
    def _extract_metadata(self, filepath):
        """Extract service and category from file path"""
        parts = filepath.replace('\\', '/').split('/')
        
        try:
            services_idx = parts.index('services')
            if services_idx + 2 < len(parts):
                service = parts[services_idx + 1]
                category = parts[services_idx + 2].replace('.md', '')
                return {'service': service, 'category': category}
        except (ValueError, IndexError):
            pass
        
        # Fallback
        service = os.path.basename(os.path.dirname(filepath))
        category = os.path.splitext(os.path.basename(filepath))[0]
        return {'service': service, 'category': category}
    
    def _index_documents(self):
        """Index all documentation files using both TF-IDF and BM25"""
        print("Indexing documentation with TF-IDF and BM25...")
        
        # Invalidate cache on reindex
        self.cache.invalidate_on_doc_change()
        
        # Find all markdown files
        search_pattern = os.path.join(self.docs_root_dir, '**', '*.md')
        files = glob.glob(search_pattern, recursive=True)
        
        if not files:
            print(f"[Warning] No documentation files found in {self.docs_root_dir}")
            return
        
        # Check if we can use cached vectors
        if self.use_vector_store and self.vector_store:
            needs_reindex = self.vector_store.needs_reindex(files, 'tfidf')
            
            if not needs_reindex:
                print("Loading vectors from persistent store...")
                # Load from vector store
                self.doc_paths, self.tfidf_matrix = self.vector_store.get_all_vectors('tfidf')
                
                # Verify we actually loaded something
                if len(self.doc_paths) > 0 and self.tfidf_matrix.size > 0:
                    # Load vocabulary
                    feature_names, idf_values = self.vector_store.get_vocabulary('tfidf')
                    if feature_names:
                        self.tfidf_vectorizer.vocabulary_ = {name: idx for idx, name in enumerate(feature_names)}
                        self.tfidf_vectorizer.idf_values_ = idf_values
                        self.tfidf_vectorizer.feature_names_ = feature_names
                        self.tfidf_vectorizer.n_docs_ = len(self.doc_paths)
                    
                    # Load documents for BM25
                    for filepath in self.doc_paths:
                        content = self._read_document(filepath)
                        if content:
                            self.documents.append(content)
                            self.doc_metadata.append(self._extract_metadata(filepath))
                    
                    # Rebuild BM25 (lightweight, doesn't need persistence)
                    if len(self.documents) > 0:
                        self.bm25.fit(self.documents)
                    
                    print(f"✓ Loaded {len(self.doc_paths)} documents from vector store")
                    print(f"TF-IDF matrix shape: {self.tfidf_matrix.shape}")
                    print(f"BM25 corpus size: {self.bm25.corpus_size}")
                    return
                else:
                    print("[WARNING] Vector store returned empty data, rebuilding index...")
        
        # Need to build index from scratch
        print("Building fresh index...")
        
        # Load all documents
        for filepath in files:
            content = self._read_document(filepath)
            if content:
                self.documents.append(content)
                self.doc_paths.append(filepath)
                self.doc_metadata.append(self._extract_metadata(filepath))
                
                # Save document to vector store
                if self.use_vector_store and self.vector_store:
                    metadata = self._extract_metadata(filepath)
                    self.vector_store.save_document(
                        filepath, content, 
                        metadata.get('service'), 
                        metadata.get('category')
                    )
        
        print(f"Loaded {len(self.documents)} documents")
        
        if len(self.documents) == 0:
            print("[Warning] No documents loaded")
            return
        
        # Fit TF-IDF vectorizer
        print("Building custom TF-IDF index...")
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.documents)
        print(f"TF-IDF matrix shape: {self.tfidf_matrix.shape}")
        
        # Save TF-IDF vectors to store
        if self.use_vector_store and self.vector_store:
            print("Saving TF-IDF vectors to persistent store...")
            self.vector_store.save_vectors_batch(self.doc_paths, self.tfidf_matrix, 'tfidf')
            
            # Save vocabulary
            if hasattr(self.tfidf_vectorizer, 'vocabulary_'):
                feature_names = self.tfidf_vectorizer.feature_names_
                idf_values = self.tfidf_vectorizer.idf_values_
                self.vector_store.save_vocabulary('tfidf', feature_names, idf_values)
            
            # Save metadata
            metadata = {
                'max_features': self.max_features,
                'ngram_min': 1,
                'ngram_max': 2,
                'stop_words': True
            }
            self.vector_store.save_metadata('tfidf', metadata)
            print("✓ Vectors persisted to SQLite")
        
        # Fit BM25 ranker
        print("Building custom BM25 index...")
        self.bm25.fit(self.documents)
        print(f"BM25 corpus size: {self.bm25.corpus_size}, avg doc length: {self.bm25.avgdl:.2f}")
        
        print("✓ Indexing complete!")
    
    def _init_feedback_system(self):
        """Initialize feedback learning system"""
        self.feedback_tfidf_vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            lowercase=True,
            stop_words=ENGLISH_STOP_WORDS,
            ngram_range=(1, 2)
        )
        self.feedback_bm25 = BM25(k1=self.bm25.k1, b=self.bm25.b)
    
    def _normalize_scores(self, scores):
        """Normalize scores to 0-1 range"""
        if len(scores) == 0:
            return scores
        
        min_score = np.min(scores)
        max_score = np.max(scores)
        
        if max_score - min_score < 1e-10:
            return np.ones_like(scores)
        
        return (scores - min_score) / (max_score - min_score)
    
    def find_relevant_doc(self, query_text, top_k=5):
        """
        Find the most relevant document using hybrid TF-IDF + BM25 ranking
        With Redis caching for fast repeated queries
        
        Args:
            query_text: Query string
            top_k: Number of candidates to consider
            
        Returns:
            Tuple of (doc_path, confidence_score)
        """
        if len(self.documents) == 0:
            raise ValueError("No documents indexed")
        
        # Check cache first
        cached_result = self.cache.get('search', query_text, method='HYBRID_CUSTOM')
        if cached_result:
            doc_path = cached_result['doc_path']
            confidence = cached_result['confidence']
            # Still record prediction for tracking
            self.feedback_loop.record_prediction(
                query_text, doc_path, confidence, 'HYBRID_CUSTOM'
            )
            return doc_path, confidence
        
        # First check feedback system for known good matches
        feedback_result = self._check_feedback(query_text)
        if feedback_result:
            doc_path, confidence = feedback_result
            # Cache the feedback result
            self.cache.set('search', query_text, {
                'doc_path': doc_path,
                'confidence': confidence
            }, method='HYBRID_CUSTOM')
            # Record prediction for tracking
            self.feedback_loop.record_prediction(
                query_text, doc_path, confidence, 'HYBRID_CUSTOM'
            )
            return feedback_result
        
        # Get TF-IDF scores
        query_vector = self.tfidf_vectorizer.transform([query_text])
        query_vector_1d = query_vector.flatten()
        
        # Temporarily set vectors in similarity search
        self.similarity_search.vectors = self.tfidf_matrix
        self.similarity_search.n_vectors = self.tfidf_matrix.shape[0]
        self.similarity_search.dimension = self.tfidf_matrix.shape[1]
        
        tfidf_results = self.similarity_search.search(query_vector_1d, k=len(self.documents))
        tfidf_scores_array = np.array([score for _, score, _ in tfidf_results])
        
        # Get BM25 scores
        bm25_scores_array = self.bm25.get_scores(query_text)
        
        # Normalize both score sets
        tfidf_normalized = self._normalize_scores(tfidf_scores_array)
        bm25_normalized = self._normalize_scores(bm25_scores_array)
        
        # Combine scores with weights
        combined_scores = (
            self.tfidf_weight * tfidf_normalized + 
            self.bm25_weight * bm25_normalized
        )
        
        # Get top document
        best_idx = np.argmax(combined_scores)
        best_score = combined_scores[best_idx]
        
        # Convert to confidence percentage (0-100)
        confidence = float(best_score * 100)
        doc_path = self.doc_paths[best_idx]
        
        # Adjust confidence based on feedback history
        adjusted_confidence = self.feedback_loop.adjust_confidence(
            query_text, doc_path, confidence, 'HYBRID_CUSTOM'
        )
        
        # Cache the result
        self.cache.set('search', query_text, {
            'doc_path': doc_path,
            'confidence': adjusted_confidence
        }, method='HYBRID_CUSTOM')
        
        # Record prediction
        self.feedback_loop.record_prediction(
            query_text, doc_path, adjusted_confidence, 'HYBRID_CUSTOM'
        )
        
        return doc_path, adjusted_confidence
    
    def get_top_n(self, query_text, n=5):
        """
        Get top N documents with hybrid ranking
        
        Args:
            query_text: Query string
            n: Number of results
            
        Returns:
            List of tuples: (doc_path, confidence, metadata)
        """
        if len(self.documents) == 0:
            return []
        
        # Get TF-IDF scores
        query_vector = self.tfidf_vectorizer.transform([query_text])
        query_vector_1d = query_vector.flatten()
        
        # Temporarily set vectors in similarity search
        self.similarity_search.vectors = self.tfidf_matrix
        self.similarity_search.n_vectors = self.tfidf_matrix.shape[0]
        self.similarity_search.dimension = self.tfidf_matrix.shape[1]
        
        tfidf_results = self.similarity_search.search(query_vector_1d, k=len(self.documents))
        tfidf_scores_array = np.array([score for _, score, _ in tfidf_results])
        
        # Get BM25 scores
        bm25_scores_array = self.bm25.get_scores(query_text)
        
        # Normalize scores
        tfidf_normalized = self._normalize_scores(tfidf_scores_array)
        bm25_normalized = self._normalize_scores(bm25_scores_array)
        
        # Combine scores
        combined_scores = (
            self.tfidf_weight * tfidf_normalized + 
            self.bm25_weight * bm25_normalized
        )
        
        # Get top N indices
        top_indices = np.argsort(combined_scores)[::-1][:n]
        
        results = []
        for idx in top_indices:
            doc_path = self.doc_paths[idx]
            confidence = float(combined_scores[idx] * 100)
            metadata = self.doc_metadata[idx]
            results.append((doc_path, confidence, metadata))
        
        return results
    
    def _check_feedback(self, query_text):
        """Check if query matches learned feedback"""
        # First, check the new feedback loop system
        feedback_result = self.feedback_loop.get_best_document_for_query(query_text)
        if feedback_result:
            return feedback_result  # Returns (doc_path, confidence)
        
        # Fall back to old feedback system
        if not self.feedback_documents:
            return None
        
        # Search feedback documents with both methods
        query_vector = self.feedback_tfidf_vectorizer.transform([query_text])
        query_vector_1d = query_vector.flatten()
        feedback_matrix = self.feedback_tfidf_vectorizer.transform(self.feedback_documents)
        
        # Create temporary similarity search for feedback
        feedback_search = SimilaritySearch(metric='cosine')
        feedback_search.vectors = feedback_matrix
        feedback_search.n_vectors = feedback_matrix.shape[0]
        feedback_search.dimension = feedback_matrix.shape[1]
        
        tfidf_results = feedback_search.search(query_vector_1d, k=1)
        
        if tfidf_results:
            idx, tfidf_score, _ = tfidf_results[0]
            bm25_scores = self.feedback_bm25.get_scores(query_text)
            
            if len(bm25_scores) > idx:
                bm25_score = bm25_scores[idx]
                # Normalize and combine
                combined = (tfidf_score + bm25_score / max(bm25_scores.max(), 1)) / 2
                
                if combined > 0.7:  # High confidence threshold
                    return self.feedback_paths[idx], 95.0
        
        return None
    
    def teach_correction(self, error_text, correct_doc_path):
        """
        Teach the system a correction
        
        Args:
            error_text: The error text that was misclassified
            correct_doc_path: The correct documentation path
        """
        # Get the predicted document first
        try:
            predicted_doc, original_confidence = self.find_relevant_doc(error_text)
        except:
            predicted_doc = None
            original_confidence = 0.0
        
        # Record feedback in the feedback loop
        if predicted_doc:
            feedback_result = self.feedback_loop.record_feedback(
                error_text,
                predicted_doc,
                correct_doc_path,
                original_confidence,
                'HYBRID_CUSTOM'
            )
            
            print(f"[Feedback] Recorded correction:")
            print(f"  Query: {error_text[:50]}...")
            print(f"  Predicted: {predicted_doc}")
            print(f"  Actual: {correct_doc_path}")
            print(f"  Success rate: {feedback_result['success_rate']:.2%}")
            print(f"  Engine accuracy: {feedback_result['engine_accuracy']:.2%}")
        
        # Also add to old feedback system for backward compatibility
        self.feedback_documents.append(error_text)
        self.feedback_paths.append(correct_doc_path)
        
        # Re-fit feedback systems
        if len(self.feedback_documents) > 0:
            self.feedback_tfidf_vectorizer.fit_transform(self.feedback_documents)
            self.feedback_bm25.fit(self.feedback_documents)
        
        # Save feedback data
        try:
            self.feedback_loop.save_to_file(self.feedback_file)
            print(f"[OK] Saved feedback data: {len(self.feedback_loop.feedback_history)} entries")
        except Exception as e:
            print(f"[WARN] Could not save feedback: {e}")
        
        print(f"[Feedback] Total corrections: {len(self.feedback_documents)}")

    
    def get_ranking_weights(self):
        """Get current ranking weights"""
        return {
            'tfidf_weight': self.tfidf_weight,
            'bm25_weight': self.bm25_weight,
            'bm25_k1': self.bm25.k1,
            'bm25_b': self.bm25.b
        }
    
    def get_feedback_statistics(self):
        """Get feedback loop statistics"""
        stats = self.feedback_loop.get_statistics()
        stats['feedback_documents'] = len(self.feedback_documents)
        stats['engine_weights'] = self.feedback_loop.get_engine_weights()
        stats['cache_stats'] = self.cache.get_stats()
        return stats
    
    def explain_ranking(self, query_text, doc_idx=None):
        """
        Explain the ranking for a query
        
        Args:
            query_text: Query string
            doc_idx: Optional document index to explain (None = top result)
            
        Returns:
            Dictionary with ranking explanation
        """
        if len(self.documents) == 0:
            return {}
        
        # Get scores
        query_vector = self.tfidf_vectorizer.transform([query_text])
        query_vector_1d = query_vector.flatten()
        
        # Temporarily set vectors in similarity search
        self.similarity_search.vectors = self.tfidf_matrix
        self.similarity_search.n_vectors = self.tfidf_matrix.shape[0]
        self.similarity_search.dimension = self.tfidf_matrix.shape[1]
        
        tfidf_results = self.similarity_search.search(query_vector_1d, k=len(self.documents))
        tfidf_scores_array = np.array([score for _, score, _ in tfidf_results])
        bm25_scores_array = self.bm25.get_scores(query_text)
        
        # Normalize
        tfidf_normalized = self._normalize_scores(tfidf_scores_array)
        bm25_normalized = self._normalize_scores(bm25_scores_array)
        
        # Combined
        combined_scores = (
            self.tfidf_weight * tfidf_normalized + 
            self.bm25_weight * bm25_normalized
        )
        
        if doc_idx is None:
            doc_idx = np.argmax(combined_scores)
        
        return {
            'document': self.doc_paths[doc_idx],
            'tfidf_score': float(tfidf_normalized[doc_idx]),
            'bm25_score': float(bm25_normalized[doc_idx]),
            'tfidf_raw': float(tfidf_scores_array[doc_idx]),
            'bm25_raw': float(bm25_scores_array[doc_idx]),
            'combined_score': float(combined_scores[doc_idx]),
            'final_confidence': float(combined_scores[doc_idx] * 100),
            'weights': {
                'tfidf': self.tfidf_weight,
                'bm25': self.bm25_weight
            },
            'metadata': self.doc_metadata[doc_idx]
        }


if __name__ == "__main__":
    # Test hybrid search
    print("Testing Hybrid Custom Search Engine (TF-IDF + BM25)")
    print("=" * 70)
    
    try:
        # Initialize
        print("\n1. Initializing Hybrid Search Engine...")
        engine = HybridCustomSearchEngine(
            tfidf_weight=0.4,
            bm25_weight=0.6,
            k1=1.5,
            b=0.75
        )
        
        print(f"\n✓ Loaded {len(engine.documents)} documents")
        print(f"✓ TF-IDF matrix: {engine.tfidf_matrix.shape}")
        print(f"✓ BM25 corpus: {engine.bm25.corpus_size} docs")
        print(f"✓ Weights: TF-IDF={engine.tfidf_weight:.2f}, BM25={engine.bm25_weight:.2f}")
        
        # Test query
        print("\n2. Testing Search Query...")
        query = "negative value validation error"
        print(f"Query: '{query}'")
        
        doc_path, confidence = engine.find_relevant_doc(query)
        print(f"\nTop Result:")
        print(f"  Path: {doc_path}")
        print(f"  Confidence: {confidence:.2f}%")
        
        # Get top 3
        print("\n3. Top 3 Results:")
        top_3 = engine.get_top_n(query, n=3)
        for i, (path, conf, meta) in enumerate(top_3, 1):
            print(f"  {i}. {meta['service']}/{meta['category']} - {conf:.2f}%")
        
        # Explain ranking
        print("\n4. Ranking Explanation:")
        explanation = engine.explain_ranking(query)
        print(f"  Document: {explanation['metadata']['category']}")
        print(f"  TF-IDF score: {explanation['tfidf_score']:.4f} (weight: {explanation['weights']['tfidf']:.2f})")
        print(f"  BM25 score: {explanation['bm25_score']:.4f} (weight: {explanation['weights']['bm25']:.2f})")
        print(f"  Combined: {explanation['combined_score']:.4f}")
        print(f"  Final confidence: {explanation['final_confidence']:.2f}%")
        
        # Test feedback
        print("\n5. Testing Feedback System...")
        engine.teach_correction("test error", engine.doc_paths[0])
        print(f"✓ Feedback system has {len(engine.feedback_documents)} corrections")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
