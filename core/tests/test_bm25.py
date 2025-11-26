"""
Tests for BM25 Ranking Algorithm
"""
import pytest
import numpy as np
from algorithms.bm25 import BM25


class TestBM25:
    """Test BM25 implementation"""
    
    def test_init(self):
        """Test BM25 initialization"""
        bm25 = BM25(k1=1.5, b=0.75)
        assert bm25.k1 == 1.5
        assert bm25.b == 0.75
        assert bm25.corpus_size == 0
    
    def test_fit(self, sample_documents):
        """Test fitting BM25 on corpus"""
        bm25 = BM25()
        bm25.fit(sample_documents)
        
        assert bm25.corpus_size == len(sample_documents)
        assert bm25.avgdl > 0
        assert len(bm25.idf) > 0
        assert len(bm25.doc_freqs) == len(sample_documents)
    
    def test_get_scores(self, sample_documents):
        """Test getting BM25 scores for query"""
        bm25 = BM25()
        bm25.fit(sample_documents)
        
        query = "python programming"
        scores = bm25.get_scores(query)
        
        assert len(scores) == len(sample_documents)
        assert all(score >= 0 for score in scores)
    
    def test_k1_parameter(self, sample_documents):
        """Test k1 parameter effect on scoring"""
        bm25_low = BM25(k1=1.0)
        bm25_high = BM25(k1=2.0)
        
        bm25_low.fit(sample_documents)
        bm25_high.fit(sample_documents)
        
        query = "python programming language"
        scores_low = bm25_low.get_scores(query)
        scores_high = bm25_high.get_scores(query)
        
        # Both should return valid scores
        assert len(scores_low) == len(sample_documents)
        assert len(scores_high) == len(sample_documents)
        assert all(score >= 0 for score in scores_low)
        assert all(score >= 0 for score in scores_high)
    
    def test_b_parameter(self, sample_documents):
        """Test b parameter for length normalization"""
        bm25_no_norm = BM25(b=0.0)
        bm25_full_norm = BM25(b=1.0)
        
        bm25_no_norm.fit(sample_documents)
        bm25_full_norm.fit(sample_documents)
        
        query = "python"
        scores_no_norm = bm25_no_norm.get_scores(query)
        scores_full_norm = bm25_full_norm.get_scores(query)
        
        # Both should return valid scores
        assert len(scores_no_norm) == len(sample_documents)
        assert len(scores_full_norm) == len(sample_documents)
        assert all(score >= 0 for score in scores_no_norm)
        assert all(score >= 0 for score in scores_full_norm)
    
    def test_query_with_unknown_terms(self, sample_documents):
        """Test query with terms not in corpus"""
        bm25 = BM25()
        bm25.fit(sample_documents)
        
        query = "unknown_term_xyz"
        scores = bm25.get_scores(query)
        
        # All scores should be 0 or very low
        assert all(score < 1.0 for score in scores)
    
    def test_empty_query(self, sample_documents):
        """Test handling of empty query"""
        bm25 = BM25()
        bm25.fit(sample_documents)
        
        scores = bm25.get_scores("")
        
        # All scores should be 0
        assert all(score == 0 for score in scores)
    
    def test_idf_calculation(self):
        """Test IDF calculation"""
        docs = ["word word", "other other", "word other"]
        bm25 = BM25()
        bm25.fit(docs)
        
        # Both terms appear in 2/3 documents
        assert 'word' in bm25.idf
        assert 'other' in bm25.idf
        assert bm25.idf['word'] > 0
        assert bm25.idf['other'] > 0
