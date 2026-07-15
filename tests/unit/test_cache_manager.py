import tempfile
from pathlib import Path

import pytest

from src.core.cache_manager import CacheManager


class TestCacheManager:
    @pytest.fixture
    def cache(self):
        CacheManager._instance = None
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        cm = CacheManager(db_path)
        cm.clear()
        yield cm
        cm._conn.close()
        Path(db_path).unlink(missing_ok=True)
        CacheManager._instance = None

    def test_put_and_get(self, cache):
        cache.put("hello world", "en-US-Standard-A", 1.0, 0.0, b"audio_data", 24000)
        result = cache.get("hello world", "en-US-Standard-A", 1.0, 0.0)
        assert result is not None
        assert result["audio_data"] == b"audio_data"
        assert result["sample_rate"] == 24000
        assert result["format"] == "wav"

    def test_get_missing(self, cache):
        result = cache.get("nonexistent", "voice", 1.0, 0.0)
        assert result is None

    def test_cache_different_voice(self, cache):
        cache.put("hello", "voice1", 1.0, 0.0, b"data1", 24000)
        cache.put("hello", "voice2", 1.0, 0.0, b"data2", 24000)
        result1 = cache.get("hello", "voice1", 1.0, 0.0)
        result2 = cache.get("hello", "voice2", 1.0, 0.0)
        assert result1["audio_data"] == b"data1"
        assert result2["audio_data"] == b"data2"

    def test_clear(self, cache):
        cache.put("hello", "voice", 1.0, 0.0, b"data", 24000)
        cache.clear()
        result = cache.get("hello", "voice", 1.0, 0.0)
        assert result is None

    def test_stats(self, cache):
        cache.put("hello", "voice", 1.0, 0.0, b"data", 24000)
        stats = cache.stats()
        assert stats["entries"] == 1
        assert stats["total_size_bytes"] > 0
