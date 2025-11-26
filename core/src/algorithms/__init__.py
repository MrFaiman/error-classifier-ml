"""
Custom ML Algorithms Package
Implements ML algorithms from scratch without blackbox libraries
"""

from .tfidf import TfidfVectorizer, ENGLISH_STOP_WORDS
from .similarity import (
    SimilaritySearch,
    cosine_similarity_matrix,
    euclidean_distance_matrix
)
from .kmeans import KMeans, elbow_method
from .text_processing import TextChunker, TextPreprocessor
from .edit_distance import EditDistance, FuzzyMatcher, fuzzy_search
from .bm25 import BM25, BM25Plus, BM25Okapi, compare_bm25_variants
from .feedback_loop import FeedbackLoop
from .feedback_database import FeedbackDatabase
from .vector_store import VectorStore

__all__ = [
    # TF-IDF
    'TfidfVectorizer',
    'ENGLISH_STOP_WORDS',
    # Similarity
    'SimilaritySearch',
    'cosine_similarity_matrix',
    'euclidean_distance_matrix',
    # Clustering
    'KMeans',
    'elbow_method',
    # Text Processing
    'TextChunker',
    'TextPreprocessor',
    # Edit Distance
    'EditDistance',
    'FuzzyMatcher',
    'fuzzy_search',
    # BM25 Ranking
    'BM25',
    'BM25Plus',
    'BM25Okapi',
    'compare_bm25_variants',
    # Feedback Loop
    'FeedbackLoop',
    'FeedbackDatabase',
    # Vector Store
    'VectorStore',
]
