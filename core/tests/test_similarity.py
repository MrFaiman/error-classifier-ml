"""
Tests for Similarity Search
"""
import pytest
import numpy as np
from algorithms.similarity import SimilaritySearch, cosine_similarity_matrix, euclidean_distance_matrix


class TestSimilarityFunctions:
    """Test similarity utility functions"""
    
    def test_cosine_similarity_matrix(self):
        """Test cosine similarity calculation"""
        X = np.array([[1, 0, 0], [0, 1, 0], [1, 1, 0]])
        Y = np.array([[1, 0, 0], [0, 0, 1]])
        
        sim = cosine_similarity_matrix(X, Y)
        
        assert sim.shape == (3, 2)
        # First vector identical to first query
        assert np.isclose(sim[0, 0], 1.0)
        # Orthogonal vectors
        assert np.isclose(sim[0, 1], 0.0)
    
    def test_euclidean_distance_matrix(self):
        """Test Euclidean distance calculation"""
        X = np.array([[0, 0], [1, 1], [2, 2]])
        Y = np.array([[0, 0], [3, 3]])
        
        dist = euclidean_distance_matrix(X, Y)
        
        assert dist.shape == (3, 2)
        # Distance to itself
        assert np.isclose(dist[0, 0], 0.0)
        # Distance between (0,0) and (3,3)
        assert np.isclose(dist[0, 1], np.sqrt(18))


class TestSimilaritySearch:
    """Test Similarity Search class"""
    
    def test_init(self):
        """Test initialization"""
        search = SimilaritySearch(metric='cosine')
        assert search.metric == 'cosine'
        assert search.vectors is None
    
    def test_fit_cosine(self):
        """Test fitting with cosine similarity"""
        search = SimilaritySearch(metric='cosine')
        vectors = np.random.rand(10, 5)
        
        search.add_vectors(vectors)
        
        assert search.n_vectors == 10
        assert search.dimension == 5
        assert search.vectors.shape == (10, 5)
    
    def test_search_cosine(self):
        """Test search with cosine similarity"""
        vectors = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 1, 0]
        ])
        
        search = SimilaritySearch(metric='cosine')
        search.add_vectors(vectors)
        
        query = np.array([1, 0, 0])
        results = search.search(query, k=2)
        
        # Should return 2 results
        assert len(results) == 2
        # First result should be identical vector (index 0)
        assert results[0][0] == 0
        assert np.isclose(results[0][1], 1.0)
    
    def test_search_euclidean(self):
        """Test search with Euclidean distance"""
        vectors = np.array([
            [0, 0],
            [1, 1],
            [2, 2],
            [3, 3]
        ])
        
        search = SimilaritySearch(metric='euclidean')
        search.add_vectors(vectors)
        
        query = np.array([0.5, 0.5])
        results = search.search(query, k=2)
        
        # Should return 2 nearest neighbors
        assert len(results) == 2
        # Closest should be [0,0] or [1,1]
        assert results[0][0] in [0, 1]
    
    def test_search_k_larger_than_corpus(self):
        """Test when k is larger than corpus size"""
        vectors = np.random.rand(5, 3)
        search = SimilaritySearch(metric='cosine')
        search.add_vectors(vectors)
        
        query = np.random.rand(3)
        results = search.search(query, k=10)
        
        # Should return all 5 vectors
        assert len(results) == 5
    
    def test_invalid_metric(self):
        """Test invalid metric raises error"""
        search = SimilaritySearch(metric='invalid')
        vectors = np.random.rand(10, 5)
        search.add_vectors(vectors)
        query = np.random.rand(5)
        with pytest.raises(ValueError):
            search.search(query, k=1)
