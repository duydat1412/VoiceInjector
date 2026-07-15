# Project Context: TTS Virtual Mic Bridge (VoiceInjector)

This document provides architectural context, tech stack details, and coding guidelines for AI agents working on this codebase.

## Project Overview

**VoiceInjector** is a desktop application written in Python (PySide6) that reads English text aloud and routes the generated speech directly into a **virtual microphone driver** (e.g., VB-CABLE on Windows, BlackHole on macOS). At the same time, it plays the audio back to the user's default speaker so they can monitor what is being sent.

This enables developers and users to test speaking practice systems or voice-activated apps automatically without having to speak into a physical mic.

---

## Tech Stack & Dependencies

- **GUI Framework:** PySide6 (Qt for Python)
- **Audio I/O:** `sounddevice` (built on PortAudio), `numpy`
- **TTS Engines:**
  - Google Translate TTS (Free, web-based, MP3 output)
  - Google Cloud TTS (Premium, API key required, WAV output)
  - Offline TTS (`pyttsx3` using SAPI5 on Windows)
- **Audio Processing:** `pydub` (used to convert Google Translate MP3 data to WAV format for PortAudio)
- **Caching:** SQLite-based caching to avoid redundant API requests

---

## Directory Structure

```text
tts-virtual-mic-bridge/
├── src/
│   ├── config/        # Settings and configurations (ConfigManager)
│   ├── core/          # Core logic (TTS engines, audio router, cache)
│   │   ├── audio_router.py   # Routes audio to virtual mic + speaker
│   │   ├── cache_manager.py  # SQLite database for audio caching
│   │   └── tts_engine.py     # TTS engine implementations
│   ├── ui/            # UI components (PySide6)
│   │   └── main_window.py    # Main GUI and worker thread management
│   ├── utils/         # Helper functions (audio device lister, logger)
│   └── main.py        # Entry point of the application
├── tests/             # Unit and integration tests (pytest)
└── requirements.txt   # Python dependencies
```

---

## Architecture & Data Flow

### 1. Main Flow (Text to Speech)

```
[UI Main Window] (Main Thread)
       │
       │ 1. User clicks "Speak" / presses Ctrl+Enter
       ▼
[MainWindow._on_speak]
       │
       │ 2. Captures GUI state (voice, rate, devices)
       │ 3. Instantiates & starts SpeakThread (QThread)
       ▼
[SpeakThread] (Worker Thread)
       │
       │ 4. Check cache for wav_data
       │    ├── If found: return cached audio
       │    └── If not: call tts_engine.synthesize() -> convert to WAV -> Cache
       ▼
[AudioRouter.play] (Blocks worker thread)
       │
       │ 5. Plays WAV to Virtual Mic and Speaker simultaneously using PortAudio
       ▼
[MainWindow._on_speak_finished] (Main Thread)
       │
       │ 6. Receives finished signal -> resets UI status to "Done ✓"
```

### 2. Threading Rules (CRITICAL)

To prevent application hangs, deadlocks, and segfaults:
1. **No Qt Widget access from worker threads:** The `SpeakThread` must never read or write directly to Qt widgets (like `self._voice_combo.currentText()` or `self.statusBar().showMessage()`). All settings must be read on the main thread and passed to the thread constructor. Updates must be sent back using Qt Signals (`Signal`).
2. **COM Initialization for Offline TTS:** Offline TTS (`pyttsx3`) on Windows uses SAPI5 via COM. When running on a non-main thread, you **must** initialize COM using `comtypes.CoInitialize()` and clean it up using `comtypes.CoUninitialize()` in the thread execution.
3. **Blocking Audio Playback:** The `AudioRouter.play()` method blocks the calling thread using `threading.Event` until playback finishes. This keeps the thread active during speaking. **Never** call this blocking method on the main thread.

---

## Guidelines for Future Enhancements

- **Adding a TTS Engine:** Implement the `BaseTTSEngine` class in `src/core/tts_engine.py`. Make sure it returns raw `WAV` data in a `TTSResult`. If the engine returns another format, handle the conversion to WAV (like the MP3 to WAV conversion done for Google Translate).
- **Virtual Audio Drivers:** The app detects virtual devices using keywords (like "cable", "voicemeeter", "blackhole"). If a new driver is released, add its keyword to `src/utils/device_utils.py` in `list_virtual_output_devices()`.
