"""
Tests for Redis Cache
"""
import pytest
from cache import RedisCache


class TestRedisCache:
    """Test Redis cache layer"""
    
    def test_init_disabled(self):
        """Test cache initialization when disabled"""
        cache = RedisCache(enabled=False)
        assert cache.enabled == False
        assert cache.redis_client is None
    
    def test_init_no_url(self):
        """Test cache initialization without URL"""
        cache = RedisCache(redis_url=None, enabled=True)
        assert cache.enabled == False
    
    def test_cache_get_when_disabled(self):
        """Test get returns None when disabled"""
        cache = RedisCache(enabled=False)
        result = cache.get('test', 'query')
        assert result is None
    
    def test_cache_set_when_disabled(self):
        """Test set does nothing when disabled"""
        cache = RedisCache(enabled=False)
        # Should not raise error
        cache.set('test', 'query', {'data': 'value'})
    
    def test_generate_key(self):
        """Test cache key generation"""
        cache = RedisCache(enabled=False)
        
        key1 = cache._generate_key('search', 'test query')
        key2 = cache._generate_key('search', 'test query')
        key3 = cache._generate_key('search', 'different query')
        
        # Same query should generate same key
        assert key1 == key2
        # Different query should generate different key
        assert key1 != key3
        # Keys should have prefix
        assert key1.startswith('search:')
    
    def test_query_normalization(self):
        """Test query normalization in key generation"""
        cache = RedisCache(enabled=False)
        
        key1 = cache._generate_key('search', '  Test   Query  ')
        key2 = cache._generate_key('search', 'test query')
        
        # Whitespace normalization
        assert key1 == key2
    
    def test_get_stats(self):
        """Test statistics retrieval"""
        cache = RedisCache(enabled=False)
        
        stats = cache.get_stats()
        
        assert 'enabled' in stats
        assert stats['enabled'] == False
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['hit_rate'] == 0.0
    
    def test_stats_tracking(self):
        """Test hit/miss statistics tracking"""
        cache = RedisCache(enabled=False)
        
        # When disabled, stats still have basic structure
        stats = cache.get_stats()
        assert stats['enabled'] == False
        assert 'hits' in stats
        assert 'misses' in stats
        assert 'hit_rate' in stats
        assert stats['hits'] == 0
        assert stats['misses'] == 0
    
    def test_invalidate_on_doc_change(self):
        """Test cache invalidation"""
        cache = RedisCache(enabled=False)
        # Should not raise error
        cache.invalidate_on_doc_change()
    
    def test_clear_all(self):
        """Test clearing entire cache"""
        cache = RedisCache(enabled=False)
        # Should not raise error
        cache.clear_all()
    
    def test_close(self):
        """Test closing cache connection"""
        cache = RedisCache(enabled=False)
        # Should not raise error
        cache.close()
