# VoiceInjector - Project Context

## Overview
Desktop app (Windows) that reads English text aloud into a virtual microphone (VB-CABLE), enabling automated testing of web-based speaking practice systems.

## Tech Stack
- **Python 3.10+** with **PySide6** (Qt GUI)
- **sounddevice** (PortAudio) for audio routing
- **pyttsx3** (offline TTS) + **aiohttp** (Google Translate TTS) + **google-cloud-texttospeech** (high quality)
- **SQLite** (WAL mode) for audio cache
- **PyInstaller** for building .exe

## Architecture

### Design Patterns
- **Strategy**: 3 TTS engines (Google Translate, Google Cloud, Offline/pyttsx3) via `BaseTTSEngine`
- **Singleton**: CacheManager, ConfigManager, SpeechLogger
- **Factory**: `create_tts_engine()` in `src/core/tts_engine.py`
- **Queue**: QueueManager for batch text processing
- **Observer**: Qt signals for UI state updates

### Key Files
| File | Purpose |
|------|---------|
| `src/main.py` | Entry point, dark theme setup |
| `src/ui/main_window.py` | Main GUI (770+ lines, Catppuccin Mocha theme) |
| `src/core/tts_engine.py` | 3 TTS engines + factory |
| `src/core/audio_router.py` | Play WAV to selected output device |
| `src/core/cache_manager.py` | SQLite cache with LRU eviction |
| `src/core/queue_manager.py` | Async queue processor |
| `src/config/config_manager.py` | Pydantic config, JSON persistence |
| `src/utils/device_utils.py` | List/filter audio devices |
| `src/utils/logger.py` | JSONL speech logging |

### TTS Engines
- **`google_translate`** (default): Free, no API key, text ≤200 chars, needs internet
- **`google_cloud`**: High quality, needs service-account.json, needs internet
- **`offline`**: pyttsx3 (Windows SAPI), works offline, lower quality

## Running

```powershell
# Run from source
python -m src.main

# Run tests
pytest tests/unit/ -v

# Build EXE (test first then build)
pytest tests/unit/ -q
pyinstaller --onefile --windowed --name "VoiceInjector" `
  --hidden-import "PySide6.QtCore" --hidden-import "PySide6.QtGui" --hidden-import "PySide6.QtWidgets" `
  --hidden-import "sounddevice" --hidden-import "numpy" --hidden-import "pyttsx3" --hidden-import "aiohttp" `
  --hidden-import "pydantic" --hidden-import "src.core.tts_engine" --hidden-import "src.core.audio_router" `
  --hidden-import "src.core.cache_manager" --hidden-import "src.core.queue_manager" `
  --hidden-import "src.config.config_manager" --hidden-import "src.utils.logger" `
  --hidden-import "src.utils.device_utils" --add-data "src;src" --paths . src\main.py
```

## CI/CD
- **GitHub Actions** (`.github/workflows/ci.yml`): on push to main
  1. `test`: pytest on Windows Python 3.11
  2. `build`: PyInstaller → EXE → upload artifact + create/update release

## Virtual Microphone Setup
- User must install [VB-CABLE](https://vb-audio.com/Cable/)
- App plays to **CABLE Input** (output device)
- Web app selects **CABLE Output** (microphone input)

## Style Guidelines
- Python: black (line-length=100), flake8 (E203,W503 ignored)
- UI: Catppuccin Mocha dark theme, no emoji icons, custom QSS stylesheet
- No comments in code unless asked
