"""
Custom K-Means Clustering Implementation from Scratch
Unsupervised learning algorithm for grouping similar documents
"""
import numpy as np
from typing import List, Tuple, Optional


class KMeans:
    """
    K-Means clustering algorithm implementation from scratch
    
    K-Means partitions n observations into k clusters where each observation 
    belongs to the cluster with the nearest mean (cluster centroid).
    
    Algorithm:
    1. Initialize k centroids randomly
    2. Assign each point to nearest centroid
    3. Update centroids to mean of assigned points
    4. Repeat steps 2-3 until convergence
    """
    
    def __init__(self, n_clusters=3, max_iter=300, tol=1e-4, random_state=None):
        """
        Initialize K-Means clustering
        
        Args:
            n_clusters: Number of clusters to form
            max_iter: Maximum number of iterations
            tol: Tolerance for convergence (change in centroid positions)
            random_state: Random seed for reproducibility
        """
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.tol = tol
        self.random_state = random_state
        
        # Fitted attributes
        self.centroids = None
        self.labels_ = None
        self.inertia_ = 0  # Sum of squared distances to nearest centroid
        self.n_iter_ = 0
        
    def _initialize_centroids(self, X: np.ndarray, method='kmeans++'):
        """
        Initialize cluster centroids
        
        Args:
            X: Data matrix of shape (n_samples, n_features)
            method: Initialization method ('random' or 'kmeans++')
        """
        n_samples = X.shape[0]
        
        if self.random_state is not None:
            np.random.seed(self.random_state)
        
        if method == 'random':
            # Randomly select k samples as initial centroids
            indices = np.random.choice(n_samples, self.n_clusters, replace=False)
            centroids = X[indices].copy()
        
        elif method == 'kmeans++':
            # K-means++ initialization (better than random)
            centroids = []
            
            # Choose first centroid randomly
            first_idx = np.random.choice(n_samples)
            centroids.append(X[first_idx])
            
            # Choose remaining centroids
            for _ in range(1, self.n_clusters):
                # Calculate distance from each point to nearest existing centroid
                distances = np.array([
                    min([self._euclidean_distance(x, c) for c in centroids])
                    for x in X
                ])
                
                # Probability proportional to squared distance
                probabilities = distances ** 2
                probabilities /= probabilities.sum()
                
                # Choose next centroid
                next_idx = np.random.choice(n_samples, p=probabilities)
                centroids.append(X[next_idx])
            
            centroids = np.array(centroids)
        
        else:
            raise ValueError(f"Unknown initialization method: {method}")
        
        return centroids
    
    def _euclidean_distance(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """Calculate Euclidean distance between two vectors"""
        return np.sqrt(np.sum((x1 - x2) ** 2))
    
    def _assign_clusters(self, X: np.ndarray) -> np.ndarray:
        """
        Assign each sample to nearest centroid
        
        Args:
            X: Data matrix of shape (n_samples, n_features)
            
        Returns:
            Array of cluster labels for each sample
        """
        n_samples = X.shape[0]
        labels = np.zeros(n_samples, dtype=int)
        
        for i, sample in enumerate(X):
            # Calculate distance to each centroid
            distances = [self._euclidean_distance(sample, centroid) 
                        for centroid in self.centroids]
            
            # Assign to nearest centroid
            labels[i] = np.argmin(distances)
        
        return labels
    
    def _update_centroids(self, X: np.ndarray, labels: np.ndarray) -> np.ndarray:
        """
        Update centroids to mean of assigned samples
        
        Args:
            X: Data matrix of shape (n_samples, n_features)
            labels: Cluster assignments for each sample
            
        Returns:
            New centroid positions
        """
        new_centroids = np.zeros_like(self.centroids)
        
        for k in range(self.n_clusters):
            # Get all samples assigned to cluster k
            cluster_samples = X[labels == k]
            
            if len(cluster_samples) > 0:
                # Update centroid to mean of cluster samples
                new_centroids[k] = cluster_samples.mean(axis=0)
            else:
                # If cluster is empty, keep old centroid or reinitialize
                new_centroids[k] = self.centroids[k]
        
        return new_centroids
    
    def _calculate_inertia(self, X: np.ndarray, labels: np.ndarray) -> float:
        """
        Calculate inertia (within-cluster sum of squares)
        
        Args:
            X: Data matrix
            labels: Cluster assignments
            
        Returns:
            Total inertia value
        """
        inertia = 0.0
        
        for k in range(self.n_clusters):
            cluster_samples = X[labels == k]
            if len(cluster_samples) > 0:
                # Sum of squared distances from samples to centroid
                distances_squared = np.sum((cluster_samples - self.centroids[k]) ** 2, axis=1)
                inertia += distances_squared.sum()
        
        return inertia
    
    def fit(self, X: np.ndarray):
        """
        Fit K-Means clustering to data
        
        Args:
            X: Data matrix of shape (n_samples, n_features)
        """
        n_samples, n_features = X.shape
        
        if self.n_clusters > n_samples:
            raise ValueError(f"n_clusters ({self.n_clusters}) cannot be larger than n_samples ({n_samples})")
        
        # Initialize centroids using k-means++
        self.centroids = self._initialize_centroids(X, method='kmeans++')
        
        # Iterative optimization
        for iteration in range(self.max_iter):
            # Assign samples to nearest centroid
            labels = self._assign_clusters(X)
            
            # Update centroids
            new_centroids = self._update_centroids(X, labels)
            
            # Check for convergence
            centroid_shift = np.linalg.norm(new_centroids - self.centroids)
            self.centroids = new_centroids
            
            if centroid_shift < self.tol:
                self.n_iter_ = iteration + 1
                break
        else:
            self.n_iter_ = self.max_iter
        
        # Final assignment and inertia calculation
        self.labels_ = self._assign_clusters(X)
        self.inertia_ = self._calculate_inertia(X, self.labels_)
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict cluster labels for new data
        
        Args:
            X: Data matrix of shape (n_samples, n_features)
            
        Returns:
            Array of predicted cluster labels
        """
        if self.centroids is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        return self._assign_clusters(X)
    
    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        """
        Fit to data and return cluster labels
        
        Args:
            X: Data matrix of shape (n_samples, n_features)
            
        Returns:
            Array of cluster labels
        """
        self.fit(X)
        return self.labels_
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Transform data to cluster-distance space
        
        Args:
            X: Data matrix of shape (n_samples, n_features)
            
        Returns:
            Distance matrix of shape (n_samples, n_clusters)
        """
        if self.centroids is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        n_samples = X.shape[0]
        distances = np.zeros((n_samples, self.n_clusters))
        
        for i, sample in enumerate(X):
            for k, centroid in enumerate(self.centroids):
                distances[i, k] = self._euclidean_distance(sample, centroid)
        
        return distances
    
    def get_cluster_info(self, X: np.ndarray) -> dict:
        """
        Get detailed information about each cluster
        
        Args:
            X: Original data matrix
            
        Returns:
            Dictionary with cluster statistics
        """
        if self.labels_ is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        cluster_info = {}
        
        for k in range(self.n_clusters):
            cluster_samples = X[self.labels_ == k]
            
            cluster_info[k] = {
                'size': len(cluster_samples),
                'centroid': self.centroids[k],
                'variance': np.var(cluster_samples, axis=0).mean() if len(cluster_samples) > 0 else 0,
                'std': np.std(cluster_samples, axis=0).mean() if len(cluster_samples) > 0 else 0
            }
        
        return cluster_info


def elbow_method(X: np.ndarray, max_k: int = 10, random_state: int = 42) -> List[Tuple[int, float]]:
    """
    Apply elbow method to find optimal number of clusters
    
    Args:
        X: Data matrix
        max_k: Maximum number of clusters to try
        random_state: Random seed
        
    Returns:
        List of (k, inertia) tuples
    """
    inertias = []
    
    for k in range(1, max_k + 1):
        kmeans = KMeans(n_clusters=k, random_state=random_state)
        kmeans.fit(X)
        inertias.append((k, kmeans.inertia_))
    
    return inertias


if __name__ == "__main__":
    # Test K-Means implementation
    print("Testing Custom K-Means Clustering")
    print("=" * 70)
    
    # Generate sample data (3 clusters)
    np.random.seed(42)
    
    # Cluster 1: centered at (0, 0)
    cluster1 = np.random.randn(50, 2) * 0.5
    
    # Cluster 2: centered at (5, 5)
    cluster2 = np.random.randn(50, 2) * 0.5 + np.array([5, 5])
    
    # Cluster 3: centered at (0, 5)
    cluster3 = np.random.randn(50, 2) * 0.5 + np.array([0, 5])
    
    X = np.vstack([cluster1, cluster2, cluster3])
    
    print(f"Data shape: {X.shape}")
    print(f"True clusters: 3")
    
    # Fit K-Means
    print("\n1. Fitting K-Means with k=3")
    print("-" * 70)
    kmeans = KMeans(n_clusters=3, random_state=42)
    kmeans.fit(X)
    
    print(f"Converged in {kmeans.n_iter_} iterations")
    print(f"Final inertia: {kmeans.inertia_:.2f}")
    print(f"\nCluster assignments: {np.bincount(kmeans.labels_)}")
    
    # Get cluster info
    print("\n2. Cluster Information")
    print("-" * 70)
    cluster_info = kmeans.get_cluster_info(X)
    for k, info in cluster_info.items():
        print(f"\nCluster {k}:")
        print(f"  Size: {info['size']} samples")
        print(f"  Centroid: [{info['centroid'][0]:.2f}, {info['centroid'][1]:.2f}]")
        print(f"  Average variance: {info['variance']:.4f}")
    
    # Predict new samples
    print("\n3. Predicting New Samples")
    print("-" * 70)
    new_samples = np.array([
        [0, 0],    # Should be cluster 0
        [5, 5],    # Should be cluster 1
        [0, 5]     # Should be cluster 2
    ])
    
    predictions = kmeans.predict(new_samples)
    print(f"New samples:\n{new_samples}")
    print(f"Predicted clusters: {predictions}")
    
    # Elbow method
    print("\n4. Elbow Method (Finding Optimal k)")
    print("-" * 70)
    elbow_results = elbow_method(X, max_k=6)
    print("k\tInertia")
    for k, inertia in elbow_results:
        print(f"{k}\t{inertia:.2f}")
    
    print("\n✅ All tests completed successfully!")
