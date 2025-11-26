"""
Custom BM25 (Best Matching 25) Implementation
Implements the BM25 ranking function from scratch for information retrieval
"""
import numpy as np
import math
from typing import List, Dict, Tuple
from collections import Counter


class BM25:
    """
    BM25 (Best Matching 25) ranking function
    
    BM25 is a probabilistic ranking function used in information retrieval
    to estimate the relevance of documents to a given search query.
    
    Formula:
    score(D,Q) = Σ IDF(qi) * (f(qi,D) * (k1 + 1)) / (f(qi,D) + k1 * (1 - b + b * |D| / avgdl))
    
    Where:
    - D = document
    - Q = query
    - qi = query term i
    - f(qi,D) = frequency of qi in D
    - |D| = length of document D
    - avgdl = average document length
    - k1 = term frequency saturation parameter (typically 1.2-2.0)
    - b = length normalization parameter (typically 0.75)
    - IDF(qi) = inverse document frequency of qi
    
    IDF(qi) = log((N - n(qi) + 0.5) / (n(qi) + 0.5) + 1)
    Where:
    - N = total number of documents
    - n(qi) = number of documents containing qi
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75, epsilon: float = 0.25):
        """
        Initialize BM25 ranker
        
        Args:
            k1: Controls term frequency saturation (default: 1.5)
                - Higher k1 = more weight on term frequency
                - Typical range: 1.2 to 2.0
            b: Controls document length normalization (default: 0.75)
                - 0 = no length normalization
                - 1 = full length normalization
                - Typical range: 0.5 to 0.8
            epsilon: Floor value for IDF (default: 0.25)
                - Prevents negative IDF scores
        """
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        
        # Will be set during fit()
        self.corpus_size = 0
        self.avgdl = 0.0
        self.doc_freqs = []  # Term frequencies per document
        self.idf = {}  # IDF scores per term
        self.doc_len = []  # Length of each document
        self.vocabulary = set()  # All unique terms
        
    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization (can be customized)
        
        Args:
            text: Input text
            
        Returns:
            List of tokens (words)
        """
        # Convert to lowercase and split on whitespace and punctuation
        text = text.lower()
        # Simple splitting - can be enhanced with regex or custom logic
        tokens = text.replace(',', ' ').replace('.', ' ').replace('!', ' ').replace('?', ' ').split()
        return tokens
    
    def _calculate_idf(self, corpus: List[List[str]]):
        """
        Calculate IDF (Inverse Document Frequency) for all terms
        
        IDF(qi) = log((N - n(qi) + 0.5) / (n(qi) + 0.5) + 1)
        
        Args:
            corpus: List of tokenized documents
        """
        # Count documents containing each term
        doc_count = {}
        
        for document in corpus:
            # Get unique terms in this document
            unique_terms = set(document)
            for term in unique_terms:
                doc_count[term] = doc_count.get(term, 0) + 1
        
        # Calculate IDF for each term
        N = self.corpus_size
        self.idf = {}
        
        for term, n_qi in doc_count.items():
            # BM25 IDF formula with smoothing
            idf_score = math.log((N - n_qi + 0.5) / (n_qi + 0.5) + 1)
            
            # Apply epsilon floor to prevent negative scores
            self.idf[term] = max(idf_score, self.epsilon)
    
    def fit(self, corpus: List[str]):
        """
        Fit BM25 on a corpus of documents
        
        Args:
            corpus: List of document strings
        """
        # Tokenize all documents
        tokenized_corpus = [self._tokenize(doc) for doc in corpus]
        
        # Calculate corpus statistics
        self.corpus_size = len(tokenized_corpus)
        self.doc_len = [len(doc) for doc in tokenized_corpus]
        self.avgdl = sum(self.doc_len) / self.corpus_size if self.corpus_size > 0 else 0
        
        # Calculate term frequencies for each document
        self.doc_freqs = []
        for doc in tokenized_corpus:
            freq_dict = Counter(doc)
            self.doc_freqs.append(freq_dict)
            self.vocabulary.update(doc)
        
        # Calculate IDF scores
        self._calculate_idf(tokenized_corpus)
    
    def _score_document(self, query_tokens: List[str], doc_idx: int) -> float:
        """
        Calculate BM25 score for a single document
        
        Args:
            query_tokens: Tokenized query
            doc_idx: Document index in corpus
            
        Returns:
            BM25 score
        """
        score = 0.0
        doc_freqs = self.doc_freqs[doc_idx]
        doc_len = self.doc_len[doc_idx]
        
        for term in query_tokens:
            if term not in self.vocabulary:
                continue
            
            # Get term frequency in document
            f_qi_D = doc_freqs.get(term, 0)
            
            if f_qi_D == 0:
                continue
            
            # Get IDF score
            idf = self.idf.get(term, 0)
            
            # Calculate BM25 component for this term
            # score(D,Q) = IDF(qi) * (f(qi,D) * (k1 + 1)) / (f(qi,D) + k1 * (1 - b + b * |D| / avgdl))
            numerator = f_qi_D * (self.k1 + 1)
            denominator = f_qi_D + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
            
            score += idf * (numerator / denominator)
        
        return score
    
    def get_scores(self, query: str) -> np.ndarray:
        """
        Calculate BM25 scores for all documents given a query
        
        Args:
            query: Query string
            
        Returns:
            Array of BM25 scores for each document
        """
        query_tokens = self._tokenize(query)
        scores = np.zeros(self.corpus_size)
        
        for idx in range(self.corpus_size):
            scores[idx] = self._score_document(query_tokens, idx)
        
        return scores
    
    def get_top_n(self, query: str, n: int = 10) -> List[Tuple[int, float]]:
        """
        Get top N documents for a query
        
        Args:
            query: Query string
            n: Number of top documents to return
            
        Returns:
            List of tuples: (document_index, score)
        """
        scores = self.get_scores(query)
        
        # Get indices sorted by score (descending)
        top_indices = np.argsort(scores)[::-1][:n]
        
        # Return tuples of (index, score)
        results = [(int(idx), float(scores[idx])) for idx in top_indices]
        
        return results
    
    def rank_documents(self, query: str, documents: List[str] = None) -> List[Tuple[int, str, float]]:
        """
        Rank documents by relevance to query
        
        Args:
            query: Query string
            documents: Optional list of documents (if None, uses fitted corpus)
            
        Returns:
            List of tuples: (index, document, score) sorted by score
        """
        if documents is not None:
            # Re-fit on new documents
            self.fit(documents)
        
        scores = self.get_scores(query)
        
        # Get original documents (need to store during fit if we want to return them)
        # For now, just return indices and scores
        results = []
        for idx in range(len(scores)):
            results.append((idx, "", float(scores[idx])))
        
        # Sort by score descending
        results.sort(key=lambda x: x[2], reverse=True)
        
        return results


class BM25Plus(BM25):
    """
    BM25+ variant with improved scoring for long documents
    
    BM25+ adds a delta parameter to prevent zero scores for query terms
    that appear in very long documents.
    
    score(D,Q) = Σ IDF(qi) * ((k1 + 1) * f(qi,D)) / (k1 * (1 - b + b * |D| / avgdl) + f(qi,D)) + delta
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75, delta: float = 1.0, epsilon: float = 0.25):
        """
        Initialize BM25+ ranker
        
        Args:
            k1: Term frequency saturation parameter
            b: Length normalization parameter
            delta: Lower bound for term scores (typically 1.0)
            epsilon: IDF floor value
        """
        super().__init__(k1, b, epsilon)
        self.delta = delta
    
    def _score_document(self, query_tokens: List[str], doc_idx: int) -> float:
        """
        Calculate BM25+ score for a single document
        
        Args:
            query_tokens: Tokenized query
            doc_idx: Document index in corpus
            
        Returns:
            BM25+ score
        """
        score = 0.0
        doc_freqs = self.doc_freqs[doc_idx]
        doc_len = self.doc_len[doc_idx]
        
        for term in query_tokens:
            if term not in self.vocabulary:
                continue
            
            f_qi_D = doc_freqs.get(term, 0)
            
            if f_qi_D == 0:
                continue
            
            idf = self.idf.get(term, 0)
            
            # BM25+ formula with delta
            numerator = (self.k1 + 1) * f_qi_D
            denominator = self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl)) + f_qi_D
            
            score += idf * ((numerator / denominator) + self.delta)
        
        return score


class BM25Okapi(BM25):
    """
    BM25Okapi - Original BM25 implementation (Okapi BM25)
    This is an alias for the standard BM25 implementation
    """
    pass


def compare_bm25_variants(corpus: List[str], query: str):
    """
    Compare different BM25 variants on the same corpus
    
    Args:
        corpus: List of documents
        query: Query string
        
    Returns:
        Dictionary with results from each variant
    """
    variants = {
        'BM25': BM25(),
        'BM25Plus': BM25Plus(),
        'BM25Okapi': BM25Okapi()
    }
    
    results = {}
    
    for name, ranker in variants.items():
        ranker.fit(corpus)
        top_docs = ranker.get_top_n(query, n=5)
        results[name] = top_docs
    
    return results


if __name__ == "__main__":
    # Test BM25 implementation
    print("Testing Custom BM25 Implementation")
    print("=" * 70)
    
    # Sample corpus
    corpus = [
        "The cat sat on the mat",
        "The dog played in the park",
        "Cats and dogs are popular pets",
        "The mat was comfortable for the cat",
        "Dogs love to play fetch in the park",
        "A cat and a dog became friends",
        "The park has many trees and flowers",
        "Pet owners love their cats and dogs"
    ]
    
    # Test 1: Basic BM25 scoring
    print("\n1. Basic BM25 Scoring")
    print("-" * 70)
    
    bm25 = BM25()
    bm25.fit(corpus)
    
    query = "cat playing in park"
    print(f"Query: '{query}'")
    print(f"Corpus size: {bm25.corpus_size}")
    print(f"Average document length: {bm25.avgdl:.2f}")
    print(f"Vocabulary size: {len(bm25.vocabulary)}")
    
    # Test 2: Get scores for all documents
    print("\n2. Document Scores")
    print("-" * 70)
    
    scores = bm25.get_scores(query)
    print(f"Query: '{query}'")
    print("\nScores for all documents:")
    for idx, (doc, score) in enumerate(zip(corpus, scores)):
        print(f"  [{idx}] {score:.4f} - {doc}")
    
    # Test 3: Get top N documents
    print("\n3. Top-N Retrieval")
    print("-" * 70)
    
    top_n = bm25.get_top_n(query, n=3)
    print(f"Query: '{query}'")
    print("\nTop 3 documents:")
    for idx, score in top_n:
        print(f"  [{idx}] {score:.4f} - {corpus[idx]}")
    
    # Test 4: Multiple queries
    print("\n4. Multiple Queries")
    print("-" * 70)
    
    queries = [
        "cat mat",
        "dog park play",
        "pet owners",
        "trees flowers"
    ]
    
    for q in queries:
        top_docs = bm25.get_top_n(q, n=2)
        print(f"\nQuery: '{q}'")
        print("  Top 2 matches:")
        for idx, score in top_docs:
            print(f"    [{idx}] {score:.4f} - {corpus[idx]}")
    
    # Test 5: Parameter tuning
    print("\n5. Parameter Tuning (k1 and b)")
    print("-" * 70)
    
    query = "cat"
    
    param_sets = [
        (1.2, 0.75, "Default-ish"),
        (2.0, 0.75, "Higher k1 (more TF weight)"),
        (1.5, 0.0, "No length normalization"),
        (1.5, 1.0, "Full length normalization")
    ]
    
    print(f"Query: '{query}'")
    for k1, b, description in param_sets:
        bm25_tuned = BM25(k1=k1, b=b)
        bm25_tuned.fit(corpus)
        top_doc = bm25_tuned.get_top_n(query, n=1)[0]
        print(f"\n  k1={k1}, b={b} ({description}):")
        print(f"    Top match: [{top_doc[0]}] {top_doc[1]:.4f}")
        print(f"    Document: {corpus[top_doc[0]]}")
    
    # Test 6: BM25+ variant
    print("\n6. BM25+ Variant")
    print("-" * 70)
    
    query = "cat dog"
    
    bm25_standard = BM25()
    bm25_standard.fit(corpus)
    
    bm25_plus = BM25Plus(delta=1.0)
    bm25_plus.fit(corpus)
    
    print(f"Query: '{query}'")
    print("\nBM25 Standard:")
    for idx, score in bm25_standard.get_top_n(query, n=3):
        print(f"  [{idx}] {score:.4f} - {corpus[idx]}")
    
    print("\nBM25+ (with delta=1.0):")
    for idx, score in bm25_plus.get_top_n(query, n=3):
        print(f"  [{idx}] {score:.4f} - {corpus[idx]}")
    
    # Test 7: IDF analysis
    print("\n7. IDF Analysis")
    print("-" * 70)
    
    print("IDF scores for common terms:")
    common_terms = ["cat", "dog", "the", "park", "mat"]
    for term in common_terms:
        idf = bm25.idf.get(term, 0)
        # Count occurrences
        doc_count = sum(1 for doc in corpus if term in doc.lower())
        print(f"  '{term}': IDF={idf:.4f} (appears in {doc_count}/{len(corpus)} docs)")
    
    # Test 8: Error handling
    print("\n8. Edge Cases")
    print("-" * 70)
    
    # Empty query
    empty_query = ""
    scores = bm25.get_scores(empty_query)
    print(f"Empty query: all scores should be 0")
    print(f"  Max score: {scores.max():.4f}, Min score: {scores.min():.4f}")
    
    # Query with unknown terms
    unknown_query = "zebra elephant giraffe"
    top_docs = bm25.get_top_n(unknown_query, n=2)
    print(f"\nQuery with unknown terms: '{unknown_query}'")
    print(f"  Top match: [{top_docs[0][0]}] {top_docs[0][1]:.4f}")
    
    # Test 9: Real-world example - Error messages
    print("\n9. Real-World Example: Error Classification")
    print("-" * 70)
    
    error_docs = [
        "ValueError: list index out of range in data processing",
        "TypeError: unsupported operand type for division",
        "IndexError: array index out of bounds during iteration",
        "KeyError: missing required field in configuration",
        "AttributeError: object has no attribute specified",
        "ValueError: invalid literal for int() with base 10"
    ]
    
    bm25_errors = BM25(k1=1.5, b=0.75)
    bm25_errors.fit(error_docs)
    
    error_query = "index out of range array"
    print(f"Query: '{error_query}'")
    print("\nTop 3 matching error types:")
    for idx, score in bm25_errors.get_top_n(error_query, n=3):
        print(f"  [{idx}] {score:.4f}")
        print(f"      {error_docs[idx]}")
    
    print("\n✅ All BM25 tests completed successfully!")
    print("\nBM25 Implementation Summary:")
    print("- Standard BM25 (Okapi BM25) with k1 and b parameters")
    print("- BM25+ variant with delta parameter")
    print("- Custom tokenization and IDF calculation")
    print("- Top-N retrieval and full scoring")
