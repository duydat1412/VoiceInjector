import json
from pathlib import Path
from typing import Optional, Any
from pydantic import BaseModel


class AppConfig(BaseModel):
    gcloud_credentials_path: str = ""
    default_voice: str = "en-US-Standard-A"
    default_device: str = ""
    speech_rate: float = 1.0
    speech_pitch: float = 0.0
    tts_engine: str = "google_translate"  # google_translate | google_cloud | offline
    dark_mode: bool = False
    cache_enabled: bool = True
    max_cache_size_mb: int = 200
    window_x: int = 100
    window_y: int = 100
    window_width: int = 550
    window_height: int = 650


class ConfigManager:
    _instance: Optional["ConfigManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._config_dir = Path.home() / ".tts-vmic-bridge"
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._config_path = self._config_dir / "settings.json"
        self._config = self._load()

    def _load(self) -> AppConfig:
        if self._config_path.exists():
            try:
                data = json.loads(self._config_path.read_text(encoding="utf-8"))
                return AppConfig(**data)
            except Exception:
                pass
        return AppConfig()

    def save(self):
        self._config_path.write_text(
            self._config.model_dump_json(indent=2), encoding="utf-8"
        )

    @property
    def config(self) -> AppConfig:
        return self._config

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        self.save()

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self._config, key, default)
