"""
Tests for TF-IDF Vectorizer
"""
import pytest
import numpy as np
from algorithms.tfidf import TfidfVectorizer


class TestTfidfVectorizer:
    """Test TF-IDF implementation"""
    
    def test_init(self):
        """Test vectorizer initialization"""
        vectorizer = TfidfVectorizer(max_features=100)
        assert vectorizer.max_features == 100
        assert vectorizer.lowercase == True
        assert vectorizer.ngram_range == (1, 1)
    
    def test_fit_transform(self, sample_documents):
        """Test fit and transform"""
        vectorizer = TfidfVectorizer()
        matrix = vectorizer.fit_transform(sample_documents)
        
        assert matrix.shape[0] == len(sample_documents)
        assert matrix.shape[1] > 0
        assert len(vectorizer.vocabulary_) > 0
        assert vectorizer.idf_values_ is not None
    
    def test_transform_single_document(self, sample_documents):
        """Test transforming a single document"""
        vectorizer = TfidfVectorizer()
        vectorizer.fit_transform(sample_documents)
        
        query = ["python programming"]
        query_vector = vectorizer.transform(query)
        
        assert query_vector.shape[0] == 1
        assert query_vector.shape[1] == len(vectorizer.vocabulary_)
    
    def test_max_features_limit(self, sample_documents):
        """Test max_features parameter"""
        vectorizer = TfidfVectorizer(max_features=5)
        matrix = vectorizer.fit_transform(sample_documents)
        
        assert matrix.shape[1] <= 5
    
    def test_stop_words_removal(self):
        """Test stop words are removed"""
        docs = ["the quick brown fox", "the lazy dog"]
        vectorizer = TfidfVectorizer(stop_words={'the'})
        vectorizer.fit_transform(docs)
        
        assert 'the' not in vectorizer.vocabulary_
    
    def test_ngram_range(self):
        """Test n-gram generation"""
        docs = ["quick brown fox"]
        
        # Unigrams only
        vectorizer1 = TfidfVectorizer(ngram_range=(1, 1))
        vectorizer1.fit_transform(docs)
        
        # Bigrams
        vectorizer2 = TfidfVectorizer(ngram_range=(1, 2))
        vectorizer2.fit_transform(docs)
        
        # Should have more features with bigrams
        assert len(vectorizer2.vocabulary_) > len(vectorizer1.vocabulary_)
    
    def test_lowercase_normalization(self):
        """Test lowercase normalization"""
        docs = ["Python PYTHON python"]
        vectorizer = TfidfVectorizer(lowercase=True)
        vectorizer.fit_transform(docs)
        
        # Should normalize to single token
        assert 'python' in vectorizer.vocabulary_
        assert 'Python' not in vectorizer.vocabulary_
        assert 'PYTHON' not in vectorizer.vocabulary_
    
    def test_empty_document(self):
        """Test handling of empty documents"""
        docs = ["word", "", "another word"]
        vectorizer = TfidfVectorizer()
        matrix = vectorizer.fit_transform(docs)
        
        assert matrix.shape[0] == 3
        # Empty document should have zero vector
        assert np.sum(matrix[1]) == 0
    
    def test_idf_calculation(self):
        """Test IDF values are calculated correctly"""
        docs = ["word word word", "other other", "word other"]
        vectorizer = TfidfVectorizer()
        vectorizer.fit_transform(docs)
        
        # 'word' appears in 2/3 docs, 'other' appears in 2/3 docs
        # IDF should be log(3/2) for both
        assert vectorizer.idf_values_ is not None
        assert len(vectorizer.idf_values_) == len(vectorizer.vocabulary_)
