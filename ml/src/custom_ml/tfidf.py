"""
Custom TF-IDF Implementation from Scratch
Replaces sklearn's TfidfVectorizer
"""
import numpy as np
from collections import Counter
import re


class TfidfVectorizer:
    """
    Term Frequency-Inverse Document Frequency (TF-IDF) Vectorizer
    
    TF-IDF is a numerical statistic that reflects how important a word is to a document
    in a collection of documents. It's calculated as:
    
    TF-IDF(term, doc) = TF(term, doc) × IDF(term)
    
    Where:
    - TF (Term Frequency) = (Number of times term appears in doc) / (Total terms in doc)
    - IDF (Inverse Document Frequency) = log(Total documents / Documents containing term)
    """
    
    def __init__(self, max_features=None, min_df=1, max_df=1.0, lowercase=True, 
                 stop_words=None, ngram_range=(1, 1)):
        """
        Initialize TF-IDF Vectorizer
        
        Args:
            max_features: Maximum number of features (vocabulary size). None = unlimited
            min_df: Minimum document frequency (ignore terms appearing in fewer docs)
            max_df: Maximum document frequency (ignore terms appearing in more docs)
            lowercase: Convert all text to lowercase
            stop_words: Set of words to ignore (e.g., {'the', 'a', 'an'})
            ngram_range: Tuple (min_n, max_n) for n-gram generation
        """
        self.max_features = max_features
        self.min_df = min_df
        self.max_df = max_df
        self.lowercase = lowercase
        self.stop_words = set(stop_words) if stop_words else set()
        self.ngram_range = ngram_range
        
        # Fitted attributes
        self.vocabulary_ = {}  # {word: index}
        self.idf_values_ = None  # IDF values for each term
        self.feature_names_ = []  # List of feature names
        self.n_docs_ = 0  # Number of documents seen during fit
        
    def _tokenize(self, text):
        """Tokenize text into words"""
        if self.lowercase:
            text = text.lower()
        
        # Simple tokenization: split on non-alphanumeric characters
        tokens = re.findall(r'\b\w+\b', text)
        
        # Remove stop words
        tokens = [token for token in tokens if token not in self.stop_words]
        
        return tokens
    
    def _generate_ngrams(self, tokens):
        """Generate n-grams from tokens"""
        ngrams = []
        min_n, max_n = self.ngram_range
        
        for n in range(min_n, max_n + 1):
            for i in range(len(tokens) - n + 1):
                ngram = ' '.join(tokens[i:i+n])
                ngrams.append(ngram)
        
        return ngrams
    
    def _build_vocabulary(self, documents):
        """Build vocabulary from documents"""
        # Count document frequency for each term
        doc_freq = Counter()
        all_terms = set()
        
        for doc in documents:
            tokens = self._tokenize(doc)
            ngrams = self._generate_ngrams(tokens)
            
            # Count unique terms in this document
            unique_terms = set(ngrams)
            for term in unique_terms:
                doc_freq[term] += 1
            all_terms.update(unique_terms)
        
        # Filter by document frequency
        n_docs = len(documents)
        min_count = self.min_df if isinstance(self.min_df, int) else int(self.min_df * n_docs)
        max_count = self.max_df if isinstance(self.max_df, int) else int(self.max_df * n_docs)
        
        filtered_terms = [
            term for term, freq in doc_freq.items()
            if min_count <= freq <= max_count
        ]
        
        # Limit vocabulary size
        if self.max_features and len(filtered_terms) > self.max_features:
            # Sort by document frequency and take top max_features
            filtered_terms = sorted(filtered_terms, key=lambda t: doc_freq[t], reverse=True)
            filtered_terms = filtered_terms[:self.max_features]
        
        # Create vocabulary mapping
        self.vocabulary_ = {term: idx for idx, term in enumerate(sorted(filtered_terms))}
        self.feature_names_ = sorted(filtered_terms)
        
        return doc_freq
    
    def _calculate_idf(self, doc_freq):
        """Calculate IDF values for each term in vocabulary"""
        n_docs = self.n_docs_
        idf_values = np.zeros(len(self.vocabulary_))
        
        for term, idx in self.vocabulary_.items():
            df = doc_freq[term]
            # IDF = log(n_docs / df) + 1 (smoothed version to avoid zero)
            idf = np.log(n_docs / df) + 1
            idf_values[idx] = idf
        
        return idf_values
    
    def fit(self, documents):
        """
        Learn vocabulary and IDF from training documents
        
        Args:
            documents: List of text documents
        """
        self.n_docs_ = len(documents)
        
        # Build vocabulary and get document frequencies
        doc_freq = self._build_vocabulary(documents)
        
        # Calculate IDF values
        self.idf_values_ = self._calculate_idf(doc_freq)
        
        return self
    
    def transform(self, documents):
        """
        Transform documents to TF-IDF matrix
        
        Args:
            documents: List of text documents
            
        Returns:
            np.ndarray: TF-IDF matrix of shape (n_documents, n_features)
        """
        if not self.vocabulary_:
            raise ValueError("Vectorizer not fitted. Call fit() first.")
        
        n_docs = len(documents)
        n_features = len(self.vocabulary_)
        tfidf_matrix = np.zeros((n_docs, n_features))
        
        for doc_idx, doc in enumerate(documents):
            tokens = self._tokenize(doc)
            ngrams = self._generate_ngrams(tokens)
            
            # Calculate term frequency
            term_counts = Counter(ngrams)
            total_terms = len(ngrams)
            
            if total_terms == 0:
                continue
            
            # Calculate TF-IDF for each term
            for term, count in term_counts.items():
                if term in self.vocabulary_:
                    term_idx = self.vocabulary_[term]
                    
                    # TF = term_count / total_terms
                    tf = count / total_terms
                    
                    # TF-IDF = TF × IDF
                    tfidf = tf * self.idf_values_[term_idx]
                    
                    tfidf_matrix[doc_idx, term_idx] = tfidf
        
        # L2 normalization (normalize each document vector)
        row_norms = np.linalg.norm(tfidf_matrix, axis=1, keepdims=True)
        row_norms[row_norms == 0] = 1  # Avoid division by zero
        tfidf_matrix = tfidf_matrix / row_norms
        
        return tfidf_matrix
    
    def fit_transform(self, documents):
        """
        Fit to documents and transform them
        
        Args:
            documents: List of text documents
            
        Returns:
            np.ndarray: TF-IDF matrix
        """
        self.fit(documents)
        return self.transform(documents)
    
    def get_feature_names(self):
        """Get list of feature names (terms in vocabulary)"""
        return self.feature_names_


# Common English stop words
ENGLISH_STOP_WORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
    'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
    'to', 'was', 'will', 'with', 'this', 'but', 'they', 'have', 'had',
    'what', 'when', 'where', 'who', 'which', 'why', 'how'
}


if __name__ == "__main__":
    # Test the TF-IDF implementation
    documents = [
        "The cat sat on the mat",
        "The dog sat on the log",
        "Cats and dogs are animals",
        "The mat was under the cat"
    ]
    
    print("Testing Custom TF-IDF Vectorizer")
    print("=" * 60)
    
    # Without stop words
    vectorizer = TfidfVectorizer(lowercase=True)
    tfidf_matrix = vectorizer.fit_transform(documents)
    
    print(f"\nVocabulary size: {len(vectorizer.vocabulary_)}")
    print(f"Feature names: {vectorizer.get_feature_names()[:10]}")
    print(f"\nTF-IDF Matrix shape: {tfidf_matrix.shape}")
    print(f"First document vector:\n{tfidf_matrix[0]}")
    
    # With stop words
    print("\n" + "=" * 60)
    print("With stop words removed:")
    vectorizer2 = TfidfVectorizer(lowercase=True, stop_words=ENGLISH_STOP_WORDS)
    tfidf_matrix2 = vectorizer2.fit_transform(documents)
    
    print(f"\nVocabulary size: {len(vectorizer2.vocabulary_)}")
    print(f"Feature names: {vectorizer2.get_feature_names()}")
    print(f"\nTF-IDF Matrix shape: {tfidf_matrix2.shape}")
    
    # Show TF-IDF values for each document
    print("\nTF-IDF values per document:")
    for i, doc in enumerate(documents):
        print(f"\nDocument {i+1}: '{doc}'")
        nonzero_indices = np.where(tfidf_matrix2[i] > 0)[0]
        for idx in nonzero_indices:
            term = vectorizer2.feature_names_[idx]
            value = tfidf_matrix2[i, idx]
            print(f"  {term}: {value:.4f}")
