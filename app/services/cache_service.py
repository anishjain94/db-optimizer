from typing import Dict, Any, Optional, Callable
import time
import json
import hashlib
from functools import wraps
import threading
from datetime import datetime, timedelta

class CacheService:
    """Enhanced caching service with TTL, cache invalidation, and multiple cache levels."""
    
    def __init__(self):
        self._cache = {}
        self._cache_metadata = {}
        self._lock = threading.Lock()
        
        # Cache levels with different TTLs
        self._cache_levels = {
            'schema': 360000,      # 1 hour - schema rarely changes
            'relationships': 360000, # 30 minutes - relationships change occasionally
            'statistics': 300,   # 5 minutes - statistics change frequently
            'sample_data': 360000,  # 10 minutes - sample data changes moderately
            'full_context': 360000  # 15 minutes - full context
        }
    
    def get(self, key: str, cache_level: str = 'full_context') -> Optional[Any]:
        """Get value from cache if valid."""
        with self._lock:
            if key not in self._cache:
                return None
            
            metadata = self._cache_metadata.get(key, {})
            ttl = self._cache_levels.get(cache_level, 300)
            
            # Check if cache is still valid
            if time.time() - metadata.get('timestamp', 0) > ttl:
                self._invalidate(key)
                return None
            
            return self._cache[key]
    
    def set(self, key: str, value: Any, cache_level: str = 'full_context') -> None:
        """Set value in cache with metadata."""
        with self._lock:
            self._cache[key] = value
            self._cache_metadata[key] = {
                'timestamp': time.time(),
                'cache_level': cache_level,
                'created_at': datetime.now().isoformat()
            }
    
    def _invalidate(self, key: str) -> None:
        """Remove key from cache."""
        self._cache.pop(key, None)
        self._cache_metadata.pop(key, None)
    
    def invalidate_all(self) -> None:
        """Clear all cache."""
        with self._lock:
            self._cache.clear()
            self._cache_metadata.clear()
    
    def invalidate_by_pattern(self, pattern: str) -> None:
        """Invalidate cache entries matching pattern."""
        with self._lock:
            keys_to_remove = [key for key in self._cache.keys() if pattern in key]
            for key in keys_to_remove:
                self._invalidate(key)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_entries = len(self._cache)
            total_size = sum(len(json.dumps(v)) for v in self._cache.values())
            
            # Group by cache level
            level_stats = {}
            for key, metadata in self._cache_metadata.items():
                level = metadata.get('cache_level', 'unknown')
                if level not in level_stats:
                    level_stats[level] = 0
                level_stats[level] += 1
            
            return {
                'total_entries': total_entries,
                'total_size_bytes': total_size,
                'entries_by_level': level_stats,
                'cache_levels': self._cache_levels
            }
    
    def cache_decorator(self, cache_level: str = 'full_context', key_generator: Optional[Callable] = None):
        """Decorator for caching function results."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_generator:
                    cache_key = key_generator(*args, **kwargs)
                else:
                    # Default key generation
                    key_parts = [func.__name__]
                    if args:
                        key_parts.append(str(hash(str(args))))
                    if kwargs:
                        key_parts.append(str(hash(str(sorted(kwargs.items())))))
                    cache_key = hashlib.md5('_'.join(key_parts).encode()).hexdigest()
                
                # Try to get from cache
                cached_result = self.get(cache_key, cache_level)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, cache_level)
                return result
            
            return wrapper
        return decorator

# Global cache instance
cache_service = CacheService() 
