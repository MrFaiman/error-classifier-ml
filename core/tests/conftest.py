"""
Pytest Configuration and Fixtures
"""
import pytest
import os
import sys
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))


@pytest.fixture
def sample_documents():
    """Sample documents for testing"""
    return [
        "The quick brown fox jumps over the lazy dog",
        "Python is a great programming language",
        "Machine learning and artificial intelligence",
        "Natural language processing with transformers",
        "Error handling and exception management"
    ]


@pytest.fixture
def sample_queries():
    """Sample queries for testing"""
    return [
        "fox jumps",
        "python programming",
        "machine learning",
        "error handling"
    ]


@pytest.fixture
def temp_docs_dir():
    """Create temporary documentation directory"""
    temp_dir = tempfile.mkdtemp()
    
    # Create sample markdown files
    os.makedirs(os.path.join(temp_dir, 'service1'), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, 'service2'), exist_ok=True)
    
    with open(os.path.join(temp_dir, 'service1', 'ERROR_A.md'), 'w') as f:
        f.write("# Error A\nThis is error type A for service 1")
    
    with open(os.path.join(temp_dir, 'service1', 'ERROR_B.md'), 'w') as f:
        f.write("# Error B\nThis is error type B for service 1")
    
    with open(os.path.join(temp_dir, 'service2', 'ERROR_C.md'), 'w') as f:
        f.write("# Error C\nThis is error type C for service 2")
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_redis_cache():
    """Mock Redis cache for testing"""
    from cache import RedisCache
    return RedisCache(redis_url=None, enabled=False)
