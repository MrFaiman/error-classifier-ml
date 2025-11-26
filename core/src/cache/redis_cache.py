"""
Redis Cache Layer for Search Engine
Provides fast caching for repeated queries to reduce computation
"""
import json
import hashlib
from typing import Optional, Tuple, Any
from datetime import timedelta


class RedisCache:
    """
    Redis-based caching layer for search results
    
    Features:
    - Caches query results with TTL
    - Handles serialization/deserialization
    - Graceful degradation if Redis unavailable
    - Cache invalidation on document updates
    """
    
    def __init__(self, redis_url: str = None, ttl_seconds: int = 3600, enabled: bool = True):
        """
        Initialize Redis cache
        
        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
            ttl_seconds: Time-to-live for cache entries (default: 1 hour)
            enabled: Enable/disable caching
        """
        self.enabled = enabled
        self.ttl_seconds = ttl_seconds
        self.redis_client = None
        self.cache_hits = 0
        self.cache_misses = 0
        
        if not enabled:
            print("[INFO] Redis cache disabled")
            return
        
        if not redis_url:
            print("[WARNING] No Redis URL provided, cache disabled")
            self.enabled = False
            return
        
        try:
            import redis
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            print(f"[OK] Redis cache connected: {redis_url}")
            print(f"[OK] Cache TTL: {ttl_seconds} seconds")
        except ImportError:
            print("[WARNING] redis package not installed. Install with: pip install redis")
            self.enabled = False
        except Exception as e:
            print(f"[WARNING] Redis connection failed: {e}")
            print("[INFO] Continuing without cache")
            self.enabled = False
    
    def _generate_key(self, prefix: str, query: str, **kwargs) -> str:
        """
        Generate cache key from query and parameters
        
        Args:
            prefix: Key prefix (e.g., 'search', 'classification')
            query: Query string
            **kwargs: Additional parameters to include in key
            
        Returns:
            Cache key string
        """
        # Normalize query
        normalized_query = ' '.join(query.lower().strip().split())
        
        # Create key components
        key_data = {
            'query': normalized_query,
            **kwargs
        }
        
        # Hash for consistent key length
        key_hash = hashlib.sha256(
            json.dumps(key_data, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        return f"{prefix}:{key_hash}"
    
    def get(self, prefix: str, query: str, **kwargs) -> Optional[Any]:
        """
        Get cached result
        
        Args:
            prefix: Key prefix
            query: Query string
            **kwargs: Additional parameters
            
        Returns:
            Cached value or None if not found
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            key = self._generate_key(prefix, query, **kwargs)
            cached_value = self.redis_client.get(key)
            
            if cached_value:
                self.cache_hits += 1
                return json.loads(cached_value)
            else:
                self.cache_misses += 1
                return None
        except Exception as e:
            print(f"[WARNING] Redis get error: {e}")
            return None
    
    def set(self, prefix: str, query: str, value: Any, ttl: int = None, **kwargs):
        """
        Set cache value
        
        Args:
            prefix: Key prefix
            query: Query string
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default)
            **kwargs: Additional parameters
        """
        if not self.enabled or not self.redis_client:
            return
        
        try:
            key = self._generate_key(prefix, query, **kwargs)
            ttl = ttl or self.ttl_seconds
            
            self.redis_client.setex(
                key,
                timedelta(seconds=ttl),
                json.dumps(value)
            )
        except Exception as e:
            print(f"[WARNING] Redis set error: {e}")
    
    def delete(self, prefix: str, pattern: str = "*"):
        """
        Delete cache entries matching pattern
        
        Args:
            prefix: Key prefix
            pattern: Pattern to match (default: all keys with prefix)
        """
        if not self.enabled or not self.redis_client:
            return
        
        try:
            full_pattern = f"{prefix}:{pattern}"
            keys = self.redis_client.keys(full_pattern)
            
            if keys:
                self.redis_client.delete(*keys)
                print(f"[INFO] Deleted {len(keys)} cache entries matching {full_pattern}")
        except Exception as e:
            print(f"[WARNING] Redis delete error: {e}")
    
    def clear_all(self):
        """Clear all cache entries"""
        if not self.enabled or not self.redis_client:
            return
        
        try:
            self.redis_client.flushdb()
            print("[INFO] Cache cleared")
        except Exception as e:
            print(f"[WARNING] Redis clear error: {e}")
    
    def get_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        if not self.enabled:
            return {
                'enabled': False,
                'hits': 0,
                'misses': 0,
                'hit_rate': 0.0
            }
        
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0.0
        
        stats = {
            'enabled': True,
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'total_requests': total,
            'hit_rate': round(hit_rate, 2)
        }
        
        # Get Redis info if available
        if self.redis_client:
            try:
                info = self.redis_client.info('memory')
                stats['used_memory_human'] = info.get('used_memory_human', 'N/A')
                stats['keys_count'] = self.redis_client.dbsize()
            except Exception as e:
                print(f"[WARNING] Could not get Redis stats: {e}")
        
        return stats
    
    def invalidate_on_doc_change(self):
        """Invalidate all search caches when documents change"""
        self.delete('search')
        self.delete('classification')
        print("[INFO] Cache invalidated due to document change")
    
    def close(self):
        """Close Redis connection"""
        if self.redis_client:
            try:
                self.redis_client.close()
                print("[INFO] Redis connection closed")
            except Exception as e:
                print(f"[WARNING] Error closing Redis: {e}")
