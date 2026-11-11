"""
AstraTrack AI - Multi-Tier Memory & Cache Engine
Provides ultra-fast in-memory LRU/TTL caching with persistent fallback.
Caches HTML search engine results, cosmos catalog queries, client telemetry, and LLM responses.
"""

import time
import threading
import json
import logging
from typing import Any, Optional, Dict, Tuple
from collections import OrderedDict

logger = logging.getLogger(__name__)


class MemoryCache:
    """
    High-performance in-memory cache with Least Recently Used (LRU) eviction
    and Time-To-Live (TTL) expiration support.
    """
    def __init__(self, max_size: int = 1000, default_ttl_sec: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl_sec
        self._lock = threading.RLock()
        # Storage: key -> (value, expire_timestamp)
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "expirations": 0}

    def get(self, key: str) -> Optional[Any]:
        """Fetch item from memory cache if not expired. Updates LRU order."""
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            value, expires_at = self._cache[key]
            now = time.time()

            if now > expires_at:
                # Expired
                del self._cache[key]
                self._stats["expirations"] += 1
                self._stats["misses"] += 1
                return None

            # Move to most recently used
            self._cache.move_to_end(key)
            self._stats["hits"] += 1
            return value

    def set(self, key: str, value: Any, ttl_sec: Optional[int] = None) -> None:
        """Store item in memory cache with optional custom TTL."""
        ttl = ttl_sec if ttl_sec is not None else self.default_ttl
        expires_at = time.time() + ttl

        with self._lock:
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self.max_size:
                # Evict least recently used (first item)
                self._cache.popitem(last=False)
                self._stats["evictions"] += 1

            self._cache[key] = (value, expires_at)

    def delete(self, key: str) -> bool:
        """Remove an item from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all in-memory cache items."""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """Remove all expired entries and return the count removed."""
        now = time.time()
        removed = 0
        with self._lock:
            keys = list(self._cache.keys())
            for k in keys:
                _, exp = self._cache[k]
                if now > exp:
                    del self._cache[k]
                    removed += 1
        return removed

    def get_stats(self) -> Dict[str, Any]:
        """Return cache performance metrics."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_ratio = (self._stats["hits"] / total_requests) if total_requests > 0 else 0.0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_ratio_percent": round(hit_ratio * 100, 2),
                "evictions": self._stats["evictions"],
                "expirations": self._stats["expirations"]
            }


# Global memory cache instances by namespace
search_cache = MemoryCache(max_size=500, default_ttl_sec=1800)       # 30 mins for HTML search
cosmos_cache = MemoryCache(max_size=2000, default_ttl_sec=86400)     # 24 hours for cosmos DB queries
client_memory_cache = MemoryCache(max_size=500, default_ttl_sec=3600) # 1 hour for client active context
