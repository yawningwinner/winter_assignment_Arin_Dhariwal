from functools import lru_cache
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

class CacheManager:
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
        self._default_ttl = timedelta(minutes=15)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if it exists and hasn't expired"""
        if key in self._cache:
            timestamp = self._timestamps.get(key)
            if timestamp and datetime.now() - timestamp < self._default_ttl:
                return self._cache[key]
            else:
                # Clean up expired entry
                self.delete(key)
        return None

    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> None:
        """Set value in cache with optional TTL"""
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
        if ttl:
            self._default_ttl = ttl

    def delete(self, key: str) -> None:
        """Remove value from cache"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)

    def clear(self) -> None:
        """Clear all cached values"""
        self._cache.clear()
        self._timestamps.clear()

# Create global cache instance
cache_manager = CacheManager()

# Decorator for caching function results
def cached(ttl: Optional[timedelta] = None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_result = cache_manager.get(key)
            if cached_result is not None:
                return cached_result
            
            # Calculate result and cache it
            result = func(*args, **kwargs)
            cache_manager.set(key, result, ttl)
            return result
        return wrapper
    return decorator 