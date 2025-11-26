# Redis Cache Layer

## Overview

The search engine now includes a Redis caching layer for fast retrieval of repeated queries. This dramatically improves response times for common error messages.

## Performance Benefits

- **Cache Hit**: < 5ms (10-50x faster)
- **Cache Miss**: 20-50ms (normal search)
- **Typical Hit Rate**: 60-80% in production

## Setup

### 1. Install Redis

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
```

**Docker:**
```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

### 2. Install Python Redis Client

```bash
pip install redis
```

### 3. Configure Environment Variables

Create/update `.env` file:
```bash
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_ENABLED=true
REDIS_CACHE_TTL=3600  # 1 hour
```

## Configuration

### Environment Variables

- `REDIS_URL`: Redis connection URL (default: `redis://localhost:6379/0`)
- `REDIS_CACHE_ENABLED`: Enable/disable caching (default: `true`)
- `REDIS_CACHE_TTL`: Cache entry TTL in seconds (default: `3600`)

### Programmatic Configuration

```python
from search_engines import HybridCustomSearchEngine

engine = HybridCustomSearchEngine(
    use_cache=True,
    redis_url='redis://localhost:6379/0'
)
```

## Cache Behavior

### What Gets Cached

- Search query results (doc_path + confidence)
- Cached per query string (normalized)
- TTL: 1 hour by default

### Cache Invalidation

Cache is automatically invalidated when:
- Documents are reindexed
- System detects document changes
- TTL expires

Manual invalidation:
```python
engine.cache.invalidate_on_doc_change()  # Clear all search caches
engine.cache.clear_all()                 # Clear entire cache
```

## Monitoring

### Cache Statistics

View cache performance in the status endpoint:

```bash
curl http://localhost:3100/api/status
```

Response includes:
```json
{
  "feedback_loop": {
    "cache_stats": {
      "enabled": true,
      "hits": 1234,
      "misses": 567,
      "total_requests": 1801,
      "hit_rate": 68.52,
      "used_memory_human": "1.2M",
      "keys_count": 42
    }
  }
}
```

### Redis CLI Monitoring

```bash
# Connect to Redis
redis-cli

# Monitor cache operations in real-time
MONITOR

# View all keys
KEYS search:*

# Get cache stats
INFO stats
```

## Production Deployment

### Docker Compose

Redis is automatically included in docker-compose:

```bash
docker-compose up -d
```

### High Availability

For production, consider:
- Redis Sentinel for automatic failover
- Redis Cluster for horizontal scaling
- Persistent storage with AOF or RDB

### Memory Management

Set max memory and eviction policy:
```bash
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## Graceful Degradation

The system works without Redis:
- Cache automatically disabled if Redis unavailable
- Falls back to normal search (no caching)
- Logs warnings but continues operation
- Zero impact on functionality

## Troubleshooting

### Cache Not Working

1. Check Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

2. Check environment variables:
```python
from constants import REDIS_URL, REDIS_CACHE_ENABLED
print(f"URL: {REDIS_URL}, Enabled: {REDIS_CACHE_ENABLED}")
```

3. Check logs for connection errors:
```
[WARNING] Redis connection failed: ...
```

### Clear Stuck Cache

```bash
redis-cli FLUSHDB
```

### Performance Issues

- Increase `REDIS_CACHE_TTL` for longer caching
- Reduce if seeing stale results
- Monitor memory usage: `redis-cli INFO memory`

## Development

Disable caching during development:
```bash
export REDIS_CACHE_ENABLED=false
```

Or in code:
```python
engine = HybridCustomSearchEngine(use_cache=False)
```
