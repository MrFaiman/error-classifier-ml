"""
Custom Similarity Search Implementation from Scratch
Replaces FAISS and implements various similarity metrics
"""
import numpy as np
from typing import List, Tuple, Optional


class SimilaritySearch:
    """
    Custom vector similarity search implementation
    Supports multiple similarity metrics and efficient search
    """
    
    def __init__(self, metric='cosine'):
        """
        Initialize similarity search
        
        Args:
            metric: Similarity metric to use ('cosine', 'euclidean', 'dot_product')
        """
        self.metric = metric
        self.vectors = None
        self.metadata = []
        self.n_vectors = 0
        self.dimension = 0
        
    def add_vectors(self, vectors: np.ndarray, metadata: Optional[List] = None):
        """
        Add vectors to the search index
        
        Args:
            vectors: numpy array of shape (n_vectors, dimension)
            metadata: Optional list of metadata for each vector
        """
        if self.vectors is None:
            self.vectors = vectors
            self.dimension = vectors.shape[1]
        else:
            if vectors.shape[1] != self.dimension:
                raise ValueError(f"Vector dimension mismatch: expected {self.dimension}, got {vectors.shape[1]}")
            self.vectors = np.vstack([self.vectors, vectors])
        
        self.n_vectors = self.vectors.shape[0]
        
        # Add metadata
        if metadata is None:
            metadata = [None] * vectors.shape[0]
        self.metadata.extend(metadata)
        
    def cosine_similarity(self, query_vector: np.ndarray, vectors: np.ndarray) -> np.ndarray:
        """
        Calculate cosine similarity between query and all vectors
        
        Cosine Similarity = (A · B) / (||A|| × ||B||)
        
        Args:
            query_vector: Query vector of shape (dimension,)
            vectors: Database vectors of shape (n_vectors, dimension)
            
        Returns:
            Similarity scores of shape (n_vectors,)
        """
        # Normalize query vector
        query_norm = np.linalg.norm(query_vector)
        if query_norm == 0:
            return np.zeros(vectors.shape[0])
        query_normalized = query_vector / query_norm
        
        # Normalize database vectors
        vector_norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vector_norms[vector_norms == 0] = 1  # Avoid division by zero
        vectors_normalized = vectors / vector_norms
        
        # Compute dot product (cosine similarity for normalized vectors)
        similarities = np.dot(vectors_normalized, query_normalized)
        
        return similarities
    
    def euclidean_distance(self, query_vector: np.ndarray, vectors: np.ndarray) -> np.ndarray:
        """
        Calculate Euclidean distance between query and all vectors
        
        Euclidean Distance = sqrt(sum((A - B)²))
        
        Args:
            query_vector: Query vector of shape (dimension,)
            vectors: Database vectors of shape (n_vectors, dimension)
            
        Returns:
            Distance scores of shape (n_vectors,)
        """
        # Calculate squared differences
        diff = vectors - query_vector
        squared_diff = diff ** 2
        
        # Sum along feature dimension and take square root
        distances = np.sqrt(np.sum(squared_diff, axis=1))
        
        return distances
    
    def dot_product(self, query_vector: np.ndarray, vectors: np.ndarray) -> np.ndarray:
        """
        Calculate dot product between query and all vectors
        
        Dot Product = sum(A × B)
        
        Args:
            query_vector: Query vector of shape (dimension,)
            vectors: Database vectors of shape (n_vectors, dimension)
            
        Returns:
            Dot product scores of shape (n_vectors,)
        """
        scores = np.dot(vectors, query_vector)
        return scores
    
    def search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[int, float, any]]:
        """
        Search for k most similar vectors
        
        Args:
            query_vector: Query vector of shape (dimension,)
            k: Number of results to return
            
        Returns:
            List of tuples (index, score, metadata) sorted by similarity
        """
        if self.vectors is None or self.n_vectors == 0:
            return []
        
        if query_vector.shape[0] != self.dimension:
            raise ValueError(f"Query vector dimension mismatch: expected {self.dimension}, got {query_vector.shape[0]}")
        
        # Calculate similarity/distance based on metric
        if self.metric == 'cosine':
            scores = self.cosine_similarity(query_vector, self.vectors)
            # Higher is better for cosine similarity
            top_k_indices = np.argsort(scores)[::-1][:k]
        elif self.metric == 'euclidean':
            scores = self.euclidean_distance(query_vector, self.vectors)
            # Lower is better for distance metrics
            top_k_indices = np.argsort(scores)[:k]
        elif self.metric == 'dot_product':
            scores = self.dot_product(query_vector, self.vectors)
            # Higher is better for dot product
            top_k_indices = np.argsort(scores)[::-1][:k]
        else:
            raise ValueError(f"Unknown metric: {self.metric}")
        
        # Prepare results
        results = []
        for idx in top_k_indices:
            score = float(scores[idx])
            metadata = self.metadata[idx] if idx < len(self.metadata) else None
            results.append((int(idx), score, metadata))
        
        return results
    
    def batch_search(self, query_vectors: np.ndarray, k: int = 5) -> List[List[Tuple[int, float, any]]]:
        """
        Search for multiple queries at once
        
        Args:
            query_vectors: Query vectors of shape (n_queries, dimension)
            k: Number of results per query
            
        Returns:
            List of result lists, one per query
        """
        results = []
        for query in query_vectors:
            results.append(self.search(query, k))
        return results
    
    def get_vector(self, index: int) -> np.ndarray:
        """Get vector by index"""
        if index < 0 or index >= self.n_vectors:
            raise IndexError(f"Index {index} out of range [0, {self.n_vectors})")
        return self.vectors[index]
    
    def get_metadata(self, index: int) -> any:
        """Get metadata by index"""
        if index < 0 or index >= len(self.metadata):
            return None
        return self.metadata[index]
    
    def save(self, filepath: str):
        """Save index to disk"""
        np.savez(
            filepath,
            vectors=self.vectors,
            metadata=np.array(self.metadata, dtype=object),
            metric=self.metric,
            dimension=self.dimension
        )
    
    def load(self, filepath: str):
        """Load index from disk"""
        data = np.load(filepath, allow_pickle=True)
        self.vectors = data['vectors']
        self.metadata = list(data['metadata'])
        self.metric = str(data['metric'])
        self.dimension = int(data['dimension'])
        self.n_vectors = self.vectors.shape[0]


def cosine_similarity_matrix(matrix1: np.ndarray, matrix2: np.ndarray) -> np.ndarray:
    """
    Calculate pairwise cosine similarity between two matrices
    
    Args:
        matrix1: Shape (n1, dimension)
        matrix2: Shape (n2, dimension)
        
    Returns:
        Similarity matrix of shape (n1, n2)
    """
    # Normalize rows
    matrix1_norm = matrix1 / np.linalg.norm(matrix1, axis=1, keepdims=True)
    matrix2_norm = matrix2 / np.linalg.norm(matrix2, axis=1, keepdims=True)
    
    # Handle zero vectors
    matrix1_norm = np.nan_to_num(matrix1_norm)
    matrix2_norm = np.nan_to_num(matrix2_norm)
    
    # Compute similarity matrix
    similarity = np.dot(matrix1_norm, matrix2_norm.T)
    
    return similarity


def euclidean_distance_matrix(matrix1: np.ndarray, matrix2: np.ndarray) -> np.ndarray:
    """
    Calculate pairwise Euclidean distance between two matrices
    
    Args:
        matrix1: Shape (n1, dimension)
        matrix2: Shape (n2, dimension)
        
    Returns:
        Distance matrix of shape (n1, n2)
    """
    # Expand dimensions for broadcasting
    m1_expanded = matrix1[:, np.newaxis, :]  # (n1, 1, dimension)
    m2_expanded = matrix2[np.newaxis, :, :]  # (1, n2, dimension)
    
    # Calculate squared differences and sum
    diff = m1_expanded - m2_expanded
    squared_distances = np.sum(diff ** 2, axis=2)
    distances = np.sqrt(squared_distances)
    
    return distances


if __name__ == "__main__":
    # Test the similarity search implementation
    print("Testing Custom Similarity Search")
    print("=" * 60)
    
    # Create sample vectors
    np.random.seed(42)
    n_vectors = 100
    dimension = 128
    
    # Generate random vectors
    vectors = np.random.randn(n_vectors, dimension)
    metadata = [f"doc_{i}" for i in range(n_vectors)]
    
    # Test cosine similarity search
    print("\n1. Cosine Similarity Search")
    print("-" * 60)
    search_engine = SimilaritySearch(metric='cosine')
    search_engine.add_vectors(vectors, metadata)
    
    # Create a query (similar to first vector)
    query = vectors[0] + np.random.randn(dimension) * 0.1
    results = search_engine.search(query, k=5)
    
    print(f"Query vector dimension: {query.shape}")
    print(f"Database size: {search_engine.n_vectors} vectors")
    print(f"\nTop 5 similar vectors:")
    for idx, score, meta in results:
        print(f"  Index: {idx}, Similarity: {score:.4f}, Metadata: {meta}")
    
    # Test Euclidean distance search
    print("\n2. Euclidean Distance Search")
    print("-" * 60)
    search_engine_euclidean = SimilaritySearch(metric='euclidean')
    search_engine_euclidean.add_vectors(vectors, metadata)
    
    results_euclidean = search_engine_euclidean.search(query, k=5)
    print(f"Top 5 nearest vectors (by Euclidean distance):")
    for idx, score, meta in results_euclidean:
        print(f"  Index: {idx}, Distance: {score:.4f}, Metadata: {meta}")
    
    # Test dot product search
    print("\n3. Dot Product Search")
    print("-" * 60)
    search_engine_dot = SimilaritySearch(metric='dot_product')
    search_engine_dot.add_vectors(vectors, metadata)
    
    results_dot = search_engine_dot.search(query, k=5)
    print(f"Top 5 vectors (by dot product):")
    for idx, score, meta in results_dot:
        print(f"  Index: {idx}, Dot Product: {score:.4f}, Metadata: {meta}")
    
    # Test pairwise similarity
    print("\n4. Pairwise Cosine Similarity")
    print("-" * 60)
    subset1 = vectors[:5]
    subset2 = vectors[10:15]
    
    similarity_matrix = cosine_similarity_matrix(subset1, subset2)
    print(f"Similarity matrix shape: {similarity_matrix.shape}")
    print(f"Similarity between vector 0 and vector 10: {similarity_matrix[0, 0]:.4f}")
    
    print("\n✅ All tests completed successfully!")
