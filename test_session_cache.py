"""
Tests for session-scoped caching functionality.
"""

import time
import pytest
from src.session_cache import SessionCache, CacheEntry, CacheStats, cached_tool


class TestCacheEntry:
    """Test CacheEntry dataclass."""
    
    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(
            value="test_value",
            timestamp=time.time(),
            tool_name="test_tool",
            key="test_key"
        )
        
        assert entry.value == "test_value"
        assert entry.tool_name == "test_tool"
        assert entry.key == "test_key"
        assert entry.hit_count == 0
    
    def test_cache_entry_hit_count(self):
        """Test incrementing hit count."""
        entry = CacheEntry(
            value="test",
            timestamp=time.time(),
            tool_name="tool",
            key="key"
        )
        
        entry.hit_count += 1
        assert entry.hit_count == 1
        
        entry.hit_count += 1
        assert entry.hit_count == 2


class TestCacheStats:
    """Test CacheStats dataclass."""
    
    def test_cache_stats_creation(self):
        """Test creating cache stats."""
        stats = CacheStats()
        
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.total_entries == 0
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats(hits=8, misses=2)
        assert stats.hit_rate == 0.8
        
        stats = CacheStats(hits=0, misses=0)
        assert stats.hit_rate == 0.0
        
        stats = CacheStats(hits=10, misses=0)
        assert stats.hit_rate == 1.0
    
    def test_stats_string_representation(self):
        """Test string representation of stats."""
        stats = CacheStats(hits=10, misses=5, evictions=2, total_entries=8)
        stats_str = str(stats)
        
        assert "Hits: 10" in stats_str
        assert "Misses: 5" in stats_str
        assert "Hit Rate: 66.7%" in stats_str
        assert "Evictions: 2" in stats_str
        assert "Current Entries: 8" in stats_str


class TestSessionCache:
    """Test SessionCache functionality."""
    
    def test_cache_initialization(self):
        """Test cache initialization with default values."""
        cache = SessionCache()
        
        assert cache.default_ttl == 300
        assert cache.max_size == 100
        assert cache.enabled is True
        assert len(cache._cache) == 0
    
    def test_cache_initialization_custom(self):
        """Test cache initialization with custom values."""
        cache = SessionCache(default_ttl=60, max_size=50, enabled=False)
        
        assert cache.default_ttl == 60
        assert cache.max_size == 50
        assert cache.enabled is False
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        cache = SessionCache()
        
        # Same inputs should generate same key
        key1 = cache._generate_cache_key("tool1", "arg1", "arg2")
        key2 = cache._generate_cache_key("tool1", "arg1", "arg2")
        assert key1 == key2
        
        # Different inputs should generate different keys
        key3 = cache._generate_cache_key("tool1", "arg1", "arg3")
        assert key1 != key3
        
        # Different tool names should generate different keys
        key4 = cache._generate_cache_key("tool2", "arg1", "arg2")
        assert key1 != key4
    
    def test_cache_key_with_kwargs(self):
        """Test cache key generation with keyword arguments."""
        cache = SessionCache()
        
        key1 = cache._generate_cache_key("tool", "arg1", param1="value1", param2="value2")
        key2 = cache._generate_cache_key("tool", "arg1", param2="value2", param1="value1")
        
        # Order of kwargs shouldn't matter
        assert key1 == key2
    
    def test_basic_get_set(self):
        """Test basic cache get and set operations."""
        cache = SessionCache()
        
        # Cache miss
        result = cache.get("tool1", "arg1")
        assert result is None
        assert cache.get_stats().misses == 1
        
        # Set value
        cache.set("tool1", "result1", "arg1")
        assert cache.get_stats().total_entries == 1
        
        # Cache hit
        result = cache.get("tool1", "arg1")
        assert result == "result1"
        assert cache.get_stats().hits == 1
    
    def test_cache_disabled(self):
        """Test that caching is bypassed when disabled."""
        cache = SessionCache(enabled=False)
        
        cache.set("tool1", "result1", "arg1")
        result = cache.get("tool1", "arg1")
        
        assert result is None
        assert cache.get_stats().total_entries == 0
    
    def test_cache_expiration(self):
        """Test cache entry expiration based on TTL."""
        cache = SessionCache(default_ttl=1)  # 1 second TTL
        
        cache.set("tool1", "result1", "arg1")
        
        # Should hit immediately
        result = cache.get("tool1", "arg1")
        assert result == "result1"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should miss after expiration
        result = cache.get("tool1", "arg1")
        assert result is None
        assert cache.get_stats().evictions == 1
    
    def test_tool_specific_ttl(self):
        """Test tool-specific TTL overrides."""
        cache = SessionCache(default_ttl=300)
        
        # get_pod_logs has 30 second TTL
        assert cache._tool_ttls["get_pod_logs"] == 30
        
        # list_consul_intentions has 300 second TTL
        assert cache._tool_ttls["list_consul_intentions"] == 300
        
        # match_error_pattern has 3600 second TTL
        assert cache._tool_ttls["match_error_pattern"] == 3600
    
    def test_cache_size_limit(self):
        """Test cache eviction when size limit is reached."""
        cache = SessionCache(max_size=3)
        
        # Fill cache to capacity
        cache.set("tool1", "result1", "arg1")
        cache.set("tool1", "result2", "arg2")
        cache.set("tool1", "result3", "arg3")
        
        assert cache.get_stats().total_entries == 3
        
        # Adding one more should trigger eviction
        cache.set("tool1", "result4", "arg4")
        
        assert cache.get_stats().total_entries == 3
        assert cache.get_stats().evictions == 1
    
    def test_lru_eviction(self):
        """Test that LRU (least recently used) entry is evicted."""
        cache = SessionCache(max_size=3)
        
        # Add three entries
        cache.set("tool1", "result1", "arg1")
        cache.set("tool1", "result2", "arg2")
        cache.set("tool1", "result3", "arg3")
        
        # Access first entry to make it recently used
        cache.get("tool1", "arg1")
        
        # Add fourth entry - should evict arg2 (least recently used)
        cache.set("tool1", "result4", "arg4")
        
        # arg1 should still be cached
        assert cache.get("tool1", "arg1") == "result1"
        
        # arg2 should be evicted
        assert cache.get("tool1", "arg2") is None
    
    def test_hit_count_tracking(self):
        """Test that hit counts are tracked correctly."""
        cache = SessionCache()
        
        cache.set("tool1", "result1", "arg1")
        
        # Access multiple times
        cache.get("tool1", "arg1")
        cache.get("tool1", "arg1")
        cache.get("tool1", "arg1")
        
        # Check hit count in cache entry
        key = cache._generate_cache_key("tool1", "arg1")
        entry = cache._cache[key]
        assert entry.hit_count == 3
    
    def test_invalidate_by_tool(self):
        """Test invalidating cache entries by tool name."""
        cache = SessionCache()
        
        cache.set("tool1", "result1", "arg1")
        cache.set("tool1", "result2", "arg2")
        cache.set("tool2", "result3", "arg3")
        
        assert cache.get_stats().total_entries == 3
        
        # Invalidate tool1 entries
        cache.invalidate(tool_name="tool1")
        
        assert cache.get_stats().total_entries == 1
        assert cache.get("tool1", "arg1") is None
        assert cache.get("tool1", "arg2") is None
        assert cache.get("tool2", "arg3") == "result3"
    
    def test_invalidate_by_pattern(self):
        """Test invalidating cache entries by pattern matching."""
        cache = SessionCache()
        
        cache.set("tool1", "pod-123 is running", "pod-123")
        cache.set("tool1", "pod-456 is running", "pod-456")
        cache.set("tool1", "service-789 is healthy", "service-789")
        
        # Invalidate entries containing "pod-123"
        cache.invalidate(pattern="pod-123")
        
        assert cache.get("tool1", "pod-123") is None
        assert cache.get("tool1", "pod-456") == "pod-456 is running"
        assert cache.get("tool1", "service-789") == "service-789 is healthy"
    
    def test_clear_cache(self):
        """Test clearing all cache entries."""
        cache = SessionCache()
        
        cache.set("tool1", "result1", "arg1")
        cache.set("tool2", "result2", "arg2")
        cache.set("tool3", "result3", "arg3")
        
        assert cache.get_stats().total_entries == 3
        
        cache.clear()
        
        assert cache.get_stats().total_entries == 0
        assert len(cache._cache) == 0
    
    def test_per_tool_statistics(self):
        """Test per-tool statistics tracking."""
        cache = SessionCache()
        
        # Tool1: 2 hits, 1 miss
        cache.set("tool1", "result1", "arg1")
        cache.get("tool1", "arg1")  # hit
        cache.get("tool1", "arg1")  # hit
        cache.get("tool1", "arg2")  # miss
        
        # Tool2: 1 hit, 2 misses
        cache.set("tool2", "result2", "arg1")
        cache.get("tool2", "arg1")  # hit
        cache.get("tool2", "arg2")  # miss
        cache.get("tool2", "arg3")  # miss
        
        tool1_stats = cache.get_tool_stats("tool1")
        assert tool1_stats.hits == 2
        assert tool1_stats.misses == 1
        assert tool1_stats.hit_rate == 2/3
        
        tool2_stats = cache.get_tool_stats("tool2")
        assert tool2_stats.hits == 1
        assert tool2_stats.misses == 2
        assert tool2_stats.hit_rate == 1/3
    
    def test_cache_summary(self):
        """Test cache summary generation."""
        cache = SessionCache()
        
        cache.set("tool1", "result1", "arg1")
        cache.get("tool1", "arg1")  # hit
        cache.get("tool1", "arg2")  # miss
        
        summary = cache.get_summary()
        
        assert "Session Cache Summary" in summary
        assert "Hits: 1" in summary
        assert "Misses: 1" in summary
        assert "Hit Rate: 50%" in summary
        assert "tool1" in summary


class TestCachedToolDecorator:
    """Test the cached_tool decorator."""
    
    def test_decorator_basic(self):
        """Test basic decorator functionality."""
        cache = SessionCache()
        call_count = {"count": 0}
        
        @cached_tool(cache, "test_tool")
        def expensive_function(arg):
            call_count["count"] += 1
            return f"result_{arg}"
        
        # First call - should execute function
        result1 = expensive_function("arg1")
        assert result1 == "result_arg1"
        assert call_count["count"] == 1
        
        # Second call with same arg - should use cache
        result2 = expensive_function("arg1")
        assert result2 == "result_arg1"
        assert call_count["count"] == 1  # Not incremented
        
        # Call with different arg - should execute function
        result3 = expensive_function("arg2")
        assert result3 == "result_arg2"
        assert call_count["count"] == 2
    
    def test_decorator_with_multiple_args(self):
        """Test decorator with multiple arguments."""
        cache = SessionCache()
        
        @cached_tool(cache, "test_tool")
        def multi_arg_function(arg1, arg2, arg3="default"):
            return f"{arg1}_{arg2}_{arg3}"
        
        result1 = multi_arg_function("a", "b", "c")
        result2 = multi_arg_function("a", "b", "c")
        
        assert result1 == result2
        assert cache.get_stats().hits == 1
    
    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""
        cache = SessionCache()
        
        @cached_tool(cache, "test_tool")
        def documented_function(arg):
            """This is a test function."""
            return arg
        
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a test function."


class TestCacheIntegration:
    """Integration tests for caching system."""
    
    def test_realistic_troubleshooting_scenario(self):
        """Test cache behavior in a realistic troubleshooting scenario."""
        cache = SessionCache(default_ttl=300, max_size=50)
        
        # Simulate checking pod status multiple times
        cache.set("get_pod_status", "Pod: web-app, Status: Running", "web-app", "default")
        cache.set("get_pod_status", "Pod: api, Status: Running", "api", "default")
        
        # Simulate checking logs
        cache.set("get_pod_logs", "Log line 1\nLog line 2", "web-app", "default")
        
        # Simulate listing pods
        cache.set("list_pods", "web-app: Running\napi: Running", "default")
        
        # Simulate error pattern matching
        cache.set("match_error_pattern", "Pattern: CrashLoopBackOff", "CrashLoopBackOff")
        
        # Verify all entries are cached
        assert cache.get_stats().total_entries == 5
        
        # Simulate repeated queries (should hit cache)
        cache.get("get_pod_status", "web-app", "default")
        cache.get("get_pod_status", "web-app", "default")
        cache.get("list_pods", "default")
        
        stats = cache.get_stats()
        assert stats.hits == 3
        assert stats.hit_rate == 3/3
    
    def test_cache_invalidation_on_pod_restart(self):
        """Test invalidating cache when a pod restarts."""
        cache = SessionCache()
        
        # Cache pod status
        cache.set("get_pod_status", "Pod: web-app, Status: Running", "web-app")
        cache.set("get_pod_logs", "Old logs", "web-app")
        cache.set("describe_pod", "Old description", "web-app")
        
        # Simulate pod restart - invalidate all web-app related entries
        cache.invalidate(pattern="web-app")
        
        # All web-app entries should be invalidated
        assert cache.get("get_pod_status", "web-app") is None
        assert cache.get("get_pod_logs", "web-app") is None
        assert cache.get("describe_pod", "web-app") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
