from pathlib import Path

import pytest

from src.config.config_manager import ConfigManager, AppConfig


class TestConfigManager:
    @pytest.fixture
    def config_manager(self, monkeypatch, tmp_path):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        ConfigManager._instance = None
        cm = ConfigManager()
        cm._config_dir = tmp_path / ".tts-vmic-bridge"
        cm._config_path = cm._config_dir / "settings.json"
        cm._config_dir.mkdir(parents=True, exist_ok=True)
        cm._config = AppConfig()
        yield cm
        ConfigManager._instance = None

    def test_default_config(self, config_manager):
        cfg = config_manager.config
        assert cfg.tts_engine == "google_translate"
        assert cfg.default_voice == "en-US-Standard-A"
        assert cfg.max_cache_size_mb == 200
        assert cfg.dark_mode is False

    def test_update(self, config_manager):
        config_manager.update(tts_engine="google_cloud", dark_mode=True)
        assert config_manager.config.tts_engine == "google_cloud"
        assert config_manager.config.dark_mode is True

    def test_get(self, config_manager):
        assert config_manager.get("tts_engine") == "google_translate"
        assert config_manager.get("nonexistent", "default") == "default"

    def test_save_and_load(self, config_manager):
        config_manager.update(tts_engine="offline")
        loaded = config_manager._load()
        assert loaded.tts_engine == "offline"
