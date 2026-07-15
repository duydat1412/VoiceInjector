import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class SpeechLogger:
    _instance: Optional["SpeechLogger"] = None

    def __new__(cls, log_dir: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, log_dir: Optional[str] = None):
        if self._initialized:
            return
        self._initialized = True
        base = Path(log_dir) if log_dir else Path.home() / ".tts-vmic-bridge" / "logs"
        base.mkdir(parents=True, exist_ok=True)
        self._log_file = base / f"speech_{datetime.now().strftime('%Y%m')}.jsonl"
        self._logger = logging.getLogger("tts_vmic_bridge")
        self._logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(base / "app.log", encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        self._logger.addHandler(fh)

    def log_speech(self, text: str, voice: str, device: str, duration_ms: int, engine: str):
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "text": text,
            "text_length": len(text),
            "voice": voice,
            "device": device,
            "duration_ms": duration_ms,
            "engine": engine,
        }
        with open(self._log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._logger.info(f"Spoke {len(text)} chars via {engine} -> {device}")

    def debug(self, msg: str):
        self._logger.debug(msg)

    def info(self, msg: str):
        self._logger.info(msg)

    def warning(self, msg: str):
        self._logger.warning(msg)

    def error(self, msg: str):
        self._logger.error(msg)
