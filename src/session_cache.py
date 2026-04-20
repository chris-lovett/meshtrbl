"""
Session-scoped caching for tool results.

This module provides intelligent caching of tool results within a troubleshooting session
to avoid redundant API calls and improve response times.
"""

import time
import hashlib
import json
from typing import Any, Dict, Optional, Callable, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from functools import wraps


@dataclass
class CacheEntry:
    """A single cache entry with metadata."""
    value: Any
    timestamp: float
    hit_count: int = 0
    tool_name: str = ""
    key: str = ""


@dataclass
class CacheStats:
    """Statistics about cache usage."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_entries: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def __str__(self) -> str:
        """Format cache statistics."""
        return (
            f"Cache Stats:\n"
            f"  Hits: {self.hits}\n"
            f"  Misses: {self.misses}\n"
            f"  Hit Rate: {self.hit_rate:.1%}\n"
            f"  Evictions: {self.evictions}\n"
            f"  Current Entries: {self.total_entries}"
        )


class SessionCache:
    """
    Session-scoped cache for tool results.
    
    Features:
    - TTL-based expiration
    - LRU eviction when size limit is reached
    - Per-tool statistics
    - Smart cache key generation
    - Manual invalidation support
    """
    
    def __init__(self, 
                 default_ttl: int = 300,  # 5 minutes
                 max_size: int = 100,
                 enabled: bool = True):
        """
        Initialize the session cache.
        
        Args:
            default_ttl: Default time-to-live in seconds
            max_size: Maximum number of entries
            enabled: Whether caching is enabled
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.enabled = enabled
        
        self._cache: Dict[str, CacheEntry] = {}
        self._stats = CacheStats()
        self._tool_stats: Dict[str, CacheStats] = defaultdict(CacheStats)
        
        # Tool-specific TTL overrides
        self._tool_ttls: Dict[str, int] = {
            # Fast-changing data (shorter TTL)
            "get_pod_logs": 30,  # Logs change frequently
            "get_service_health": 60,  # Health can change quickly
            
            # Slower-changing data (longer TTL)
            "list_pods": 120,  # Pod list changes less frequently
            "describe_pod": 180,  # Pod config is relatively stable
            "list_consul_services": 180,  # Service list is stable
            "get_service_instances": 120,  # Instances change occasionally
            "list_consul_intentions": 300,  # Intentions rarely change
            "get_consul_members": 300,  # Cluster members are stable
            
            # Pattern matching (very long TTL - patterns don't change)
            "match_error_pattern": 3600,  # 1 hour
            "search_error_patterns": 3600,  # 1 hour
        }
    
    def _generate_cache_key(self, tool_name: str, *args, **kwargs) -> str:
        """
        Generate a unique cache key for a tool call.
        
        Args:
            tool_name: Name of the tool
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Cache key string
        """
        # Create a stable representation of arguments
        key_parts = [tool_name]
        
        # Add positional args
        for arg in args:
            if arg is not None:
                key_parts.append(str(arg))
        
        # Add keyword args (sorted for consistency)
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}={v}")
        
        # Hash the key for consistent length
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _is_expired(self, entry: CacheEntry, tool_name: str) -> bool:
        """
        Check if a cache entry has expired.
        
        Args:
            entry: Cache entry to check
            tool_name: Name of the tool
        
        Returns:
            True if expired, False otherwise
        """
        ttl = self._tool_ttls.get(tool_name, self.default_ttl)
        age = time.time() - entry.timestamp
        return age > ttl
    
    def _evict_lru(self):
        """Evict the least recently used entry."""
        if not self._cache:
            return
        
        # Find entry with oldest timestamp and lowest hit count
        lru_key = min(
            self._cache.keys(),
            key=lambda k: (self._cache[k].hit_count, self._cache[k].timestamp)
        )
        
        del self._cache[lru_key]
        self._stats.evictions += 1
        self._stats.total_entries = len(self._cache)
    
    def get(self, tool_name: str, *args, **kwargs) -> Optional[Any]:
        """
        Get a cached result.
        
        Args:
            tool_name: Name of the tool
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Cached value or None if not found/expired
        """
        if not self.enabled:
            return None
        
        key = self._generate_cache_key(tool_name, *args, **kwargs)
        entry = self._cache.get(key)
        
        if entry is None:
            self._stats.misses += 1
            self._tool_stats[tool_name].misses += 1
            return None
        
        # Check expiration
        if self._is_expired(entry, tool_name):
            del self._cache[key]
            self._stats.misses += 1
            self._stats.evictions += 1
            self._stats.total_entries = len(self._cache)
            self._tool_stats[tool_name].misses += 1
            return None
        
        # Cache hit
        entry.hit_count += 1
        self._stats.hits += 1
        self._tool_stats[tool_name].hits += 1
        
        return entry.value
    
    def set(self, tool_name: str, value: Any, *args, **kwargs):
        """
        Store a result in the cache.
        
        Args:
            tool_name: Name of the tool
            value: Value to cache
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        if not self.enabled:
            return
        
        # Evict if at capacity
        if len(self._cache) >= self.max_size:
            self._evict_lru()
        
        key = self._generate_cache_key(tool_name, *args, **kwargs)
        
        self._cache[key] = CacheEntry(
            value=value,
            timestamp=time.time(),
            tool_name=tool_name,
            key=key
        )
        
        self._stats.total_entries = len(self._cache)
        self._tool_stats[tool_name].total_entries = sum(
            1 for e in self._cache.values() if e.tool_name == tool_name
        )
    
    def invalidate(self, tool_name: Optional[str] = None, pattern: Optional[str] = None):
        """
        Invalidate cache entries.
        
        Args:
            tool_name: Invalidate all entries for this tool (optional)
            pattern: Invalidate entries matching this pattern (optional)
        """
        if not self.enabled:
            return
        
        if tool_name:
            # Invalidate all entries for a specific tool
            keys_to_delete = [
                k for k, v in self._cache.items() 
                if v.tool_name == tool_name
            ]
            for key in keys_to_delete:
                del self._cache[key]
                self._stats.evictions += 1
        
        elif pattern:
            # Invalidate entries matching a pattern (e.g., namespace, pod name)
            keys_to_delete = [
                k for k, v in self._cache.items()
                if pattern.lower() in str(v.value).lower()
            ]
            for key in keys_to_delete:
                del self._cache[key]
                self._stats.evictions += 1
        
        self._stats.total_entries = len(self._cache)
    
    def clear(self):
        """Clear all cache entries."""
        count = len(self._cache)
        self._cache.clear()
        self._stats.evictions += count
        self._stats.total_entries = 0
        self._tool_stats.clear()
    
    def get_stats(self) -> CacheStats:
        """Get overall cache statistics."""
        return self._stats
    
    def get_tool_stats(self, tool_name: str) -> CacheStats:
        """Get statistics for a specific tool."""
        return self._tool_stats[tool_name]
    
    def get_all_tool_stats(self) -> Dict[str, CacheStats]:
        """Get statistics for all tools."""
        return dict(self._tool_stats)
    
    def get_summary(self) -> str:
        """
        Get a human-readable summary of cache status.
        
        Returns:
            Formatted cache summary
        """
        lines = [
            "=" * 70,
            "Session Cache Summary",
            "=" * 70,
            "",
            str(self._stats),
            "",
            "Per-Tool Statistics:",
        ]
        
        # Sort tools by hit count
        sorted_tools = sorted(
            self._tool_stats.items(),
            key=lambda x: x[1].hits,
            reverse=True
        )
        
        for tool_name, stats in sorted_tools:
            if stats.hits + stats.misses > 0:
                lines.append(
                    f"  {tool_name}: "
                    f"{stats.hits} hits, {stats.misses} misses "
                    f"({stats.hit_rate:.0%} hit rate)"
                )
        
        return "\n".join(lines)


def cached_tool(cache: SessionCache, tool_name: str):
    """
    Decorator to add caching to a tool function.
    
    Args:
        cache: SessionCache instance
        tool_name: Name of the tool for cache key generation
    
    Returns:
        Decorated function with caching
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get from cache
            cached_result = cache.get(tool_name, *args, **kwargs)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(tool_name, result, *args, **kwargs)
            
            return result
        
        return wrapper
    return decorator


# Global cache instance (can be replaced per session)
_global_cache: Optional[SessionCache] = None


def get_global_cache() -> SessionCache:
    """Get or create the global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = SessionCache()
    return _global_cache


def set_global_cache(cache: SessionCache):
    """Set the global cache instance."""
    global _global_cache
    _global_cache = cache


def clear_global_cache():
    """Clear the global cache."""
    global _global_cache
    if _global_cache:
        _global_cache.clear()

# Made with Bob
