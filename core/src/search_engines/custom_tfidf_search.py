"""
Custom TF-IDF Search Engine
Uses custom TF-IDF and Cosine Similarity implementations (no blackbox libraries)
"""
import os
import glob
import numpy as np
import pandas as pd
import uuid
from constants import DOCS_ROOT_DIR
from custom_ml import TfidfVectorizer, SimilaritySearch, ENGLISH_STOP_WORDS


class CustomTfidfSearchEngine:
    """
    Error classification search engine using custom TF-IDF and cosine similarity.
    Implements all ML algorithms from scratch without blackbox libraries.
    
    Key algorithms implemented:
    1. TF-IDF (Term Frequency-Inverse Document Frequency) - Custom implementation
    2. Cosine Similarity - Custom vector similarity search
    3. Document preprocessing and tokenization
    """
    
    def __init__(self, docs_root_dir=None, max_features=5000):
        """
        Initialize custom TF-IDF search engine
        
        Args:
            docs_root_dir: Root directory containing documentation files
            max_features: Maximum vocabulary size for TF-IDF
        """
        if docs_root_dir is None:
            docs_root_dir = DOCS_ROOT_DIR
        self.docs_root_dir = docs_root_dir
        self.max_features = max_features
        
        # Initialize custom TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            lowercase=True,
            stop_words=ENGLISH_STOP_WORDS,
            ngram_range=(1, 2)  # Use unigrams and bigrams
        )
        
        # Initialize custom similarity search (cosine similarity)
        self.similarity_search = SimilaritySearch(metric='cosine')
        
        # Storage
        self.documents = []  # List of document contents
        self.doc_paths = []  # List of document file paths
        self.doc_metadata = []  # List of metadata dicts
        self.tfidf_matrix = None  # TF-IDF matrix for all documents
        
        # Feedback system
        self.feedback_vectorizer = None
        self.feedback_search = None
        self.feedback_documents = []
        self.feedback_paths = []
        
        # Index documents
        self._index_documents()
        self._init_feedback_system()
    
    def _read_document(self, filepath):
        """Read and preprocess a document file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            print(f"[Warning] Failed to read {filepath}: {e}")
            return None
    
    def _index_documents(self):
        """Index all documentation files using custom TF-IDF"""
        print("Indexing documentation with custom TF-IDF...")
        
        # Find all markdown files
        search_pattern = os.path.join(self.docs_root_dir, '**', '*.md')
        files = glob.glob(search_pattern, recursive=True)
        
        if not files:
            print(f"[Warning] No markdown files found in {self.docs_root_dir}")
            return
        
        # Read all documents
        for filepath in files:
            content = self._read_document(filepath)
            if content:
                self.documents.append(content)
                self.doc_paths.append(filepath)
                
                # Extract metadata
                filename = os.path.basename(filepath)
                service = os.path.basename(os.path.dirname(filepath))
                
                self.doc_metadata.append({
                    'source': filepath,
                    'filename': filename,
                    'service': service
                })
        
        if not self.documents:
            print("[Error] No documents were successfully indexed.")
            return
        
        # Fit TF-IDF vectorizer and transform documents
        print(f"Computing TF-IDF for {len(self.documents)} documents...")
        self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
        
        print(f"  Vocabulary size: {len(self.vectorizer.vocabulary_)}")
        print(f"  TF-IDF matrix shape: {self.tfidf_matrix.shape}")
        
        # Add document vectors to similarity search
        self.similarity_search.add_vectors(self.tfidf_matrix, self.doc_metadata)
        
        print(f"[OK] Custom TF-IDF search engine initialized successfully")
    
    def _init_feedback_system(self):
        """Initialize feedback/correction system"""
        self.feedback_documents = []
        self.feedback_paths = []
        print("  [OK] Feedback system initialized (Custom TF-IDF)")
    
    def find_relevant_doc(self, error_snippet, top_k=1):
        """
        Find most relevant document for an error using custom TF-IDF + Cosine Similarity
        
        Algorithm:
        1. Transform error text using fitted TF-IDF vectorizer
        2. Calculate cosine similarity with all document vectors
        3. Return document with highest similarity
        
        Args:
            error_snippet: Error message text
            top_k: Number of results to return (default 1)
            
        Returns:
            Tuple of (doc_path, confidence_percentage)
        """
        if not self.documents:
            return "No docs indexed", 0.0
        
        # Check feedback corrections first
        if self.feedback_documents and self.feedback_search:
            try:
                # Transform query using feedback vectorizer
                query_vector_feedback = self.feedback_vectorizer.transform([error_snippet])[0]
                
                # Search in feedback store
                feedback_results = self.feedback_search.search(query_vector_feedback, k=1)
                
                if feedback_results:
                    idx, similarity, metadata = feedback_results[0]
                    # Use strict threshold for feedback (0.7 = 70% similarity)
                    if similarity > 0.7:
                        correct_path = self.feedback_paths[idx]
                        confidence = similarity * 100
                        print(f"[Custom TF-IDF] Using learned correction (confidence: {confidence:.2f}%)")
                        return correct_path, confidence
            except Exception as e:
                # Feedback lookup failed, continue with normal search
                pass
        
        # Transform error text to TF-IDF vector
        query_vector = self.vectorizer.transform([error_snippet])[0]
        
        # Find most similar documents using custom cosine similarity
        results = self.similarity_search.search(query_vector, k=top_k)
        
        if not results:
            return "No match found", 0.0
        
        # Get best result
        best_idx, similarity_score, metadata = results[0]
        best_doc_path = self.doc_paths[best_idx]
        
        # Convert similarity to percentage (0-1 range -> 0-100%)
        confidence_percentage = similarity_score * 100
        
        return best_doc_path, confidence_percentage
    
    def teach_correction(self, error_text, correct_doc_path):
        """
        Learn from user correction using custom TF-IDF
        
        Args:
            error_text: The error message that was misclassified
            correct_doc_path: The correct documentation path
        """
        correction_id = f"correction_{uuid.uuid4().hex[:8]}"
        
        print(f"[Custom TF-IDF] Learning correction...")
        
        # Add to feedback storage
        self.feedback_documents.append(error_text)
        self.feedback_paths.append(correct_doc_path)
        
        # Refit feedback vectorizer with all corrections
        self.feedback_vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            lowercase=True,
            stop_words=ENGLISH_STOP_WORDS,
            ngram_range=(1, 2)
        )
        
        feedback_matrix = self.feedback_vectorizer.fit_transform(self.feedback_documents)
        
        # Recreate feedback search index
        self.feedback_search = SimilaritySearch(metric='cosine')
        self.feedback_search.add_vectors(
            feedback_matrix,
            [{'correction_id': correction_id, 'path': path} for path in self.feedback_paths]
        )
        
        print(f"[Custom TF-IDF] Correction learned: {correct_doc_path}")
        print(f"  Total corrections stored: {len(self.feedback_documents)}")
    
    def get_top_terms(self, error_snippet, top_n=10):
        """
        Get top N most important terms from error snippet based on TF-IDF
        
        Args:
            error_snippet: Error message text
            top_n: Number of top terms to return
            
        Returns:
            List of tuples (term, tfidf_score)
        """
        # Transform to TF-IDF
        query_vector = self.vectorizer.transform([error_snippet])[0]
        
        # Get non-zero indices
        nonzero_indices = np.where(query_vector > 0)[0]
        
        # Sort by TF-IDF value
        sorted_indices = sorted(nonzero_indices, key=lambda i: query_vector[i], reverse=True)
        
        # Get top N terms
        top_terms = []
        for idx in sorted_indices[:top_n]:
            term = self.vectorizer.feature_names_[idx]
            score = query_vector[idx]
            top_terms.append((term, score))
        
        return top_terms
    
    def explain_match(self, error_snippet, doc_index):
        """
        Explain why a document matches an error (interpretability)
        
        Args:
            error_snippet: Error message text
            doc_index: Index of the document to explain
            
        Returns:
            Dictionary with explanation details
        """
        if doc_index < 0 or doc_index >= len(self.documents):
            return {"error": "Invalid document index"}
        
        # Get TF-IDF vectors
        query_vector = self.vectorizer.transform([error_snippet])[0]
        doc_vector = self.tfidf_matrix[doc_index]
        
        # Find matching terms (both have non-zero TF-IDF)
        query_terms = set(np.where(query_vector > 0)[0])
        doc_terms = set(np.where(doc_vector > 0)[0])
        matching_terms = query_terms & doc_terms
        
        # Calculate contribution of each matching term
        term_contributions = []
        for term_idx in matching_terms:
            term = self.vectorizer.feature_names_[term_idx]
            query_weight = query_vector[term_idx]
            doc_weight = doc_vector[term_idx]
            contribution = query_weight * doc_weight
            term_contributions.append((term, contribution))
        
        # Sort by contribution
        term_contributions.sort(key=lambda x: x[1], reverse=True)
        
        # Calculate overall similarity
        similarity = np.dot(query_vector, doc_vector)
        
        return {
            'document_path': self.doc_paths[doc_index],
            'overall_similarity': float(similarity),
            'matching_terms': len(matching_terms),
            'top_contributing_terms': term_contributions[:10],
            'query_term_count': len(query_terms),
            'doc_term_count': len(doc_terms)
        }


if __name__ == "__main__":
    # Test the custom TF-IDF search engine
    print("Testing Custom TF-IDF Search Engine")
    print("=" * 70)
    
    engine = CustomTfidfSearchEngine()
    
    test_errors = [
        "signal_strength: 999 (Sensor overload)",
        "base_id: 'DROP TABLE users' (SQL Injection attempt)",
        "lat: 95.0 (GPS coordinates out of range)",
        "Invalid user input in comment field"
    ]
    
    for error_text in test_errors:
        print(f"\nError: '{error_text}'")
        doc_path, confidence = engine.find_relevant_doc(error_text)
        
        print(f"Matched Doc: {doc_path}")
        print(f"Confidence: {confidence:.2f}%")
        
        # Show top terms
        top_terms = engine.get_top_terms(error_text, top_n=5)
        print(f"Top terms: {[term for term, _ in top_terms]}")
        
        print("-" * 70)
