"""
Enhanced Custom Search Engine
Uses ALL custom ML implementations: TF-IDF, Cosine Similarity, K-Means, Edit Distance, Custom Chunking
"""
import os
import glob
import numpy as np
import pandas as pd
import uuid
from constants import DOCS_ROOT_DIR
from custom_ml import (
    TfidfVectorizer, 
    SimilaritySearch, 
    ENGLISH_STOP_WORDS,
    KMeans,
    TextChunker,
    TextPreprocessor,
    EditDistance,
    FuzzyMatcher
)


class EnhancedCustomSearchEngine:
    """
    Enhanced error classification search engine using 100% custom implementations
    
    Custom ML Algorithms Implemented:
    1. TF-IDF (Term Frequency-Inverse Document Frequency) - Custom vectorization
    2. Cosine Similarity - Custom vector similarity search
    3. K-Means Clustering - Document clustering for organization
    4. Edit Distance (Levenshtein) - Fuzzy matching for typos
    5. Custom Text Chunking - Intelligent document splitting
    6. Text Preprocessing - Custom normalization and cleaning
    
    NO BLACKBOX LIBRARIES for ML algorithms!
    """
    
    def __init__(self, docs_root_dir=None, max_features=5000, n_clusters=5, 
                 chunk_size=500, chunk_overlap=50):
        """
        Initialize enhanced custom search engine
        
        Args:
            docs_root_dir: Root directory containing documentation files
            max_features: Maximum vocabulary size for TF-IDF
            n_clusters: Number of clusters for K-Means
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        if docs_root_dir is None:
            docs_root_dir = DOCS_ROOT_DIR
        self.docs_root_dir = docs_root_dir
        self.max_features = max_features
        self.n_clusters = n_clusters
        
        # Custom implementations
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            lowercase=True,
            stop_words=ENGLISH_STOP_WORDS,
            ngram_range=(1, 2)
        )
        
        self.similarity_search = SimilaritySearch(metric='cosine')
        self.text_chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.preprocessor = TextPreprocessor()
        
        # K-Means for document clustering
        self.kmeans = None
        self.cluster_labels = None
        
        # Fuzzy matcher for error types
        self.fuzzy_matcher = None
        
        # Storage
        self.documents = []
        self.doc_paths = []
        self.doc_metadata = []
        self.chunks = []
        self.chunk_metadata = []
        self.tfidf_matrix = None
        
        # Feedback system
        self.feedback_vectorizer = None
        self.feedback_search = None
        self.feedback_documents = []
        self.feedback_paths = []
        
        # Index documents
        self._index_documents()
        self._cluster_documents()
        self._init_feedback_system()
        self._init_fuzzy_matcher()
    
    def _read_document(self, filepath):
        """Read and preprocess a document file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply custom preprocessing
            content = self.preprocessor.normalize_whitespace(content)
            return content
        except Exception as e:
            print(f"[Warning] Failed to read {filepath}: {e}")
            return None
    
    def _index_documents(self):
        """Index all documentation files using custom implementations"""
        print("Indexing documentation with custom implementations...")
        
        # Find all markdown files
        search_pattern = os.path.join(self.docs_root_dir, '**', '*.md')
        files = glob.glob(search_pattern, recursive=True)
        
        if not files:
            print(f"[Warning] No markdown files found in {self.docs_root_dir}")
            return
        
        # Read and chunk all documents
        for filepath in files:
            content = self._read_document(filepath)
            if not content:
                continue
            
            # Store original document
            self.documents.append(content)
            self.doc_paths.append(filepath)
            
            filename = os.path.basename(filepath)
            service = os.path.basename(os.path.dirname(filepath))
            
            self.doc_metadata.append({
                'source': filepath,
                'filename': filename,
                'service': service,
                'stats': self.preprocessor.get_text_stats(content)
            })
            
            # Create chunks using custom chunker
            doc_chunks = self.text_chunker.split_text(content)
            
            for chunk_idx, chunk in enumerate(doc_chunks):
                self.chunks.append(chunk)
                self.chunk_metadata.append({
                    'doc_index': len(self.documents) - 1,
                    'chunk_index': chunk_idx,
                    'total_chunks': len(doc_chunks),
                    'source': filepath,
                    'filename': filename,
                    'service': service
                })
        
        if not self.chunks:
            print("[Error] No documents were successfully indexed.")
            return
        
        # Fit TF-IDF vectorizer on chunks
        print(f"Computing custom TF-IDF for {len(self.documents)} documents ({len(self.chunks)} chunks)...")
        self.tfidf_matrix = self.vectorizer.fit_transform(self.chunks)
        
        print(f"  Vocabulary size: {len(self.vectorizer.vocabulary_)}")
        print(f"  TF-IDF matrix shape: {self.tfidf_matrix.shape}")
        
        # Add to custom similarity search
        self.similarity_search.add_vectors(self.tfidf_matrix, self.chunk_metadata)
        
        print(f"[OK] Enhanced custom search engine initialized successfully")
    
    def _cluster_documents(self):
        """Cluster documents using custom K-Means implementation"""
        if len(self.documents) < self.n_clusters:
            print(f"[Info] Too few documents ({len(self.documents)}) for {self.n_clusters} clusters. Skipping clustering.")
            return
        
        try:
            print(f"Clustering {len(self.chunks)} chunks into {self.n_clusters} groups using custom K-Means...")
            
            self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42)
            self.cluster_labels = self.kmeans.fit_predict(self.tfidf_matrix)
            
            # Get cluster info
            cluster_info = self.kmeans.get_cluster_info(self.tfidf_matrix)
            
            print(f"  Converged in {self.kmeans.n_iter_} iterations")
            print(f"  Inertia: {self.kmeans.inertia_:.2f}")
            print(f"  Cluster sizes: {[info['size'] for info in cluster_info.values()]}")
            
            # Add cluster labels to metadata
            for i, metadata in enumerate(self.chunk_metadata):
                metadata['cluster'] = int(self.cluster_labels[i])
            
            print("[OK] Custom K-Means clustering completed")
        
        except Exception as e:
            print(f"[Warning] Clustering failed: {e}")
    
    def _init_fuzzy_matcher(self):
        """Initialize fuzzy matcher with error categories"""
        error_categories = set()
        for metadata in self.doc_metadata:
            filename = metadata['filename'].replace('.md', '')
            error_categories.add(filename)
        
        self.fuzzy_matcher = FuzzyMatcher(list(error_categories), case_sensitive=False)
        print(f"[OK] Fuzzy matcher initialized with {len(error_categories)} categories")
    
    def _init_feedback_system(self):
        """Initialize feedback/correction system"""
        self.feedback_documents = []
        self.feedback_paths = []
        print("  [OK] Feedback system initialized (Enhanced Custom)")
    
    def find_relevant_doc(self, error_snippet, top_k=1, use_fuzzy=True):
        """
        Find most relevant document using custom implementations
        
        Features:
        - Custom TF-IDF + Cosine Similarity for semantic matching
        - Edit distance for fuzzy matching (handles typos)
        - K-Means cluster information for context
        
        Args:
            error_snippet: Error message text
            top_k: Number of results to return
            use_fuzzy: Whether to use fuzzy matching for typos
            
        Returns:
            Tuple of (doc_path, confidence_percentage)
        """
        if not self.chunks:
            return "No docs indexed", 0.0
        
        # Check feedback corrections first
        if self.feedback_documents and self.feedback_search:
            try:
                query_vector_feedback = self.feedback_vectorizer.transform([error_snippet])[0]
                feedback_results = self.feedback_search.search(query_vector_feedback, k=1)
                
                if feedback_results:
                    idx, similarity, metadata = feedback_results[0]
                    if similarity > 0.7:  # 70% threshold
                        correct_path = self.feedback_paths[idx]
                        confidence = similarity * 100
                        print(f"[Enhanced Custom] Using learned correction (confidence: {confidence:.2f}%)")
                        return correct_path, confidence
            except Exception:
                pass
        
        # Try fuzzy matching on error categories (for typos)
        fuzzy_boost = 1.0
        if use_fuzzy and self.fuzzy_matcher:
            error_categories = [meta['filename'].replace('.md', '') for meta in self.doc_metadata]
            
            # Check if query contains any error category with typos
            query_words = error_snippet.upper().split()
            for word in query_words:
                if len(word) > 5:  # Only check longer words
                    matches = self.fuzzy_matcher.find_matches_above_threshold(word, threshold=0.7)
                    if matches:
                        print(f"[Fuzzy Match] '{word}' matched '{matches[0][0]}' (similarity: {matches[0][1]:.2%})")
                        fuzzy_boost = 1.1  # Boost confidence
                        break
        
        # Transform using custom TF-IDF
        query_vector = self.vectorizer.transform([error_snippet])[0]
        
        # Find most similar chunks using custom cosine similarity
        results = self.similarity_search.search(query_vector, k=top_k * 3)  # Get more for aggregation
        
        if not results:
            return "No match found", 0.0
        
        # Aggregate results by document
        doc_scores = {}
        for chunk_idx, similarity, metadata in results:
            doc_path = metadata['source']
            
            if doc_path not in doc_scores:
                doc_scores[doc_path] = {
                    'total_similarity': 0,
                    'count': 0,
                    'best_similarity': 0,
                    'cluster': metadata.get('cluster', -1)
                }
            
            doc_scores[doc_path]['total_similarity'] += similarity
            doc_scores[doc_path]['count'] += 1
            doc_scores[doc_path]['best_similarity'] = max(
                doc_scores[doc_path]['best_similarity'], 
                similarity
            )
        
        # Calculate final scores (weighted average of best and mean)
        final_scores = []
        for doc_path, scores in doc_scores.items():
            avg_similarity = scores['total_similarity'] / scores['count']
            best_similarity = scores['best_similarity']
            
            # Weighted combination: 70% best chunk, 30% average
            final_score = 0.7 * best_similarity + 0.3 * avg_similarity
            final_score *= fuzzy_boost  # Apply fuzzy boost
            
            final_scores.append((doc_path, final_score))
        
        # Sort and get best
        final_scores.sort(key=lambda x: -x[1])
        best_doc_path, best_score = final_scores[0]
        
        confidence_percentage = best_score * 100
        
        return best_doc_path, confidence_percentage
    
    def teach_correction(self, error_text, correct_doc_path):
        """Learn from user correction using custom implementations"""
        correction_id = f"correction_{uuid.uuid4().hex[:8]}"
        
        print(f"[Enhanced Custom] Learning correction...")
        
        self.feedback_documents.append(error_text)
        self.feedback_paths.append(correct_doc_path)
        
        # Refit feedback vectorizer
        self.feedback_vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            lowercase=True,
            stop_words=ENGLISH_STOP_WORDS,
            ngram_range=(1, 2)
        )
        
        feedback_matrix = self.feedback_vectorizer.fit_transform(self.feedback_documents)
        
        # Recreate feedback search
        self.feedback_search = SimilaritySearch(metric='cosine')
        self.feedback_search.add_vectors(
            feedback_matrix,
            [{'correction_id': correction_id, 'path': path} for path in self.feedback_paths]
        )
        
        print(f"[Enhanced Custom] Correction learned: {correct_doc_path}")
        print(f"  Total corrections stored: {len(self.feedback_documents)}")
    
    def get_cluster_summary(self):
        """Get summary of document clusters"""
        if self.cluster_labels is None:
            return {"error": "Clustering not performed"}
        
        cluster_info = {}
        for cluster_id in range(self.n_clusters):
            chunks_in_cluster = [
                self.chunk_metadata[i] for i, label in enumerate(self.cluster_labels) if label == cluster_id
            ]
            
            # Get unique documents in cluster
            docs_in_cluster = set(chunk['source'] for chunk in chunks_in_cluster)
            
            cluster_info[f"cluster_{cluster_id}"] = {
                'num_chunks': len(chunks_in_cluster),
                'num_documents': len(docs_in_cluster),
                'documents': list(docs_in_cluster)[:5]  # Show first 5
            }
        
        return cluster_info
    
    def explain_match_with_edit_distance(self, error_snippet, doc_path):
        """
        Explain match using both TF-IDF and edit distance
        
        Args:
            error_snippet: Error message
            doc_path: Path to matched document
            
        Returns:
            Dictionary with explanation
        """
        # Find document
        doc_idx = self.doc_paths.index(doc_path) if doc_path in self.doc_paths else -1
        
        if doc_idx == -1:
            return {"error": "Document not found"}
        
        doc_content = self.documents[doc_idx]
        
        # Get TF-IDF similarity
        query_vector = self.vectorizer.transform([error_snippet])[0]
        
        # Get edit distance
        edit_dist = EditDistance.levenshtein(error_snippet, doc_content[:len(error_snippet)])
        edit_similarity = EditDistance.similarity_ratio(error_snippet, doc_content[:500])
        
        # Get top TF-IDF terms
        query_terms = []
        nonzero_indices = np.where(query_vector > 0)[0]
        for idx in nonzero_indices[:10]:
            term = self.vectorizer.feature_names_[idx]
            score = query_vector[idx]
            query_terms.append((term, float(score)))
        
        return {
            'document': doc_path,
            'edit_distance': edit_dist,
            'edit_similarity': f"{edit_similarity:.2%}",
            'top_query_terms': query_terms,
            'cluster': int(self.cluster_labels[doc_idx]) if self.cluster_labels is not None else -1,
            'doc_stats': self.doc_metadata[doc_idx]['stats']
        }


if __name__ == "__main__":
    print("Testing Enhanced Custom Search Engine")
    print("=" * 70)
    print("Using 100% Custom ML Implementations:")
    print("  ✓ Custom TF-IDF")
    print("  ✓ Custom Cosine Similarity")
    print("  ✓ Custom K-Means Clustering")
    print("  ✓ Custom Edit Distance (Levenshtein)")
    print("  ✓ Custom Text Chunking")
    print("  ✓ Custom Text Preprocessing")
    print("=" * 70)
    
    engine = EnhancedCustomSearchEngine()
    
    # Get cluster summary
    print("\nDocument Clusters:")
    cluster_summary = engine.get_cluster_summary()
    for cluster_name, info in cluster_summary.items():
        print(f"  {cluster_name}: {info['num_chunks']} chunks from {info['num_documents']} documents")
    
    # Test searches
    test_errors = [
        "signal_strength: 999 (Sensor overload)",
        "SECURTY_ALRT",  # Typo - will use fuzzy matching
        "lat: 95.0 (GPS out of range)",
    ]
    
    print("\nTest Searches:")
    for error_text in test_errors:
        print(f"\n  Query: '{error_text}'")
        doc_path, confidence = engine.find_relevant_doc(error_text, use_fuzzy=True)
        print(f"  Result: {os.path.basename(doc_path)}")
        print(f"  Confidence: {confidence:.2f}%")
