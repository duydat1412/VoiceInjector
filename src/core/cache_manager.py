import hashlib
import sqlite3
import time
from pathlib import Path
from typing import Optional


class CacheManager:
    _instance: Optional["CacheManager"] = None
    _db_path_override: Optional[str] = None

    def __new__(cls, db_path: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
            cls._db_path_override = db_path
        return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        if self._initialized:
            return
        self._initialized = True
        effective_path = db_path or self._db_path_override
        if effective_path:
            self._db_path = Path(effective_path)
        else:
            self._db_path = Path.home() / ".tts-vmic-bridge" / "cache.db"
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS audio_cache (
                key TEXT PRIMARY KEY,
                audio_data BLOB,
                sample_rate INTEGER,
                format TEXT,
                voice TEXT,
                created_at REAL,
                size_bytes INTEGER
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cache_created ON audio_cache(created_at)
        """)
        self._max_size_mb = 200

    def _make_key(self, text: str, voice: str, rate: float, pitch: float) -> str:
        raw = f"{text}||{voice}||{rate}||{pitch}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, text: str, voice: str, rate: float = 1.0, pitch: float = 0.0) -> Optional[dict]:
        key = self._make_key(text, voice, rate, pitch)
        row = self._conn.execute(
            "SELECT audio_data, sample_rate, format FROM audio_cache WHERE key = ?",
            (key,)
        ).fetchone()
        if row:
            return {
                "audio_data": row[0],
                "sample_rate": row[1],
                "format": row[2],
            }
        return None

    def put(self, text: str, voice: str, rate: float, pitch: float,
            audio_data: bytes, sample_rate: int, fmt: str = "wav"):
        key = self._make_key(text, voice, rate, pitch)
        self._conn.execute(
            """INSERT OR REPLACE INTO audio_cache
               (key, audio_data, sample_rate, format, voice, created_at, size_bytes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (key, audio_data, sample_rate, fmt, voice, time.time(), len(audio_data))
        )
        self._conn.commit()
        self._evict_if_needed()

    def clear(self):
        self._conn.execute("DELETE FROM audio_cache")
        self._conn.commit()

    def stats(self) -> dict:
        row = self._conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(size_bytes), 0) FROM audio_cache"
        ).fetchone()
        return {
            "entries": row[0],
            "total_size_bytes": row[1],
            "total_size_mb": round(row[1] / (1024 * 1024), 2),
        }

    def _evict_if_needed(self):
        stats = self.stats()
        if stats["total_size_mb"] <= self._max_size_mb:
            return
        rows = self._conn.execute(
            "SELECT key, created_at FROM audio_cache ORDER BY created_at ASC"
        ).fetchall()
        target = stats["total_size_bytes"] - int(self._max_size_mb * 0.8 * 1024 * 1024)
        deleted = 0
        for key, _ in rows:
            if deleted >= target:
                break
            self._conn.execute("DELETE FROM audio_cache WHERE key = ?", (key,))
            deleted += 1
        self._conn.commit()
