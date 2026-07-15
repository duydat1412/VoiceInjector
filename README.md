# TTS Virtual Mic Bridge

A desktop application that reads English text aloud **into a virtual microphone**, enabling you to test speaking practice systems automatically without speaking into a real mic.

## How It Works

```
User types/pastes text → TTS Engine → Audio → Virtual Microphone & Speaker → Your Speaking App & You
```

Your web-based speaking practice system simply selects the virtual mic as its audio input. The app feeds TTS audio into that virtual mic as if you were speaking, while also playing it back to your speakers so you can hear what is being sent.

## Features

- **Multiple TTS Engines**: Google Translate (free), Google Cloud (high quality), offline pyttsx3
- **Virtual Audio Routing**: Plays audio directly into VB-CABLE (Windows) or BlackHole (macOS)
- **Dual Playback**: Plays to virtual mic and default speaker/headphones simultaneously
- **Smart Caching**: Caches audio to avoid redundant API calls
- **Logging**: JSONL logs of all speech events
- **Cross-Platform**: Windows 10/11 and macOS 12+ (Intel & Apple Silicon)

## Prerequisites

### 1. Virtual Audio Driver (Required)

| OS | Driver | Download |
|----|--------|----------|
| Windows | **VB-CABLE Virtual Audio Cable** | [Download](https://vb-audio.com/Cable/) |
| macOS | **BlackHole** | `brew install blackhole-16ch` |

### 2. TTS Engine Setup

#### Option A: Google Translate (Free - Default)
- **No setup required**. Works out of the box.
- Text length limited to ~200 characters per request
- Internet connection required

#### Option B: Google Cloud TTS (High Quality)
1. Create a Google Cloud Project
2. Enable the Text-to-Speech API
3. Create a Service Account and download the JSON key
4. Set the credentials path in Settings

#### Option C: Offline (pyttsx3)
- Works offline, no API key needed
- Lower quality voice

## Installation

### From Source

```bash
# Clone
git clone https://github.com/yourusername/tts-virtual-mic-bridge.git
cd tts-virtual-mic-bridge

# Install dependencies
pip install -r requirements.txt

# Run
python src/main.py
```

### Build Executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "TTS-VMic-Bridge" src/main.py
```

The executable will be in the `dist/` folder.

## Usage

1. **Set up virtual audio**:
   - Install VB-CABLE (Windows) or BlackHole (macOS)
   - The app auto-detects virtual audio devices

2. **Configure your speaking app**:
   - Set the microphone input to "CABLE Output" (Windows) or "BlackHole" (macOS)

3. **In TTS Virtual Mic Bridge**:
   - Select the virtual mic device from the dropdown
   - Paste or type your English text
   - Click "Speak" (or press `Ctrl+Enter`)

4. **Your speaking app** will receive the audio as if you were speaking naturally, and you will hear it play back on your default speakers simultaneously.

## Settings

| Setting | Description |
|---------|-------------|
| TTS Engine | Google Translate (free), Google Cloud (API key required), Offline |
| Voice | Multiple English voices available |
| Speed | 50% - 200% speech rate |
| Google Cloud Credentials | Path to service account JSON |
| Max Cache Size | Audio cache limit |

## Project Structure

```
tts-virtual-mic-bridge/
├── src/
│   ├── core/          # TTS engines, audio router, cache
│   ├── ui/            # PySide6 GUI
│   ├── config/        # Settings management
│   ├── utils/         # Logger, device utilities
│   └── main.py        # Entry point
├── tests/             # Unit & integration tests
├── .github/workflows/ # CI/CD pipelines
└── requirements.txt
```

## Development

```bash
# Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-mock flake8 black pre-commit

# Run tests
pytest tests/ -v

# Lint
flake8 src/ tests/

# Format
black src/ tests/

# Setup pre-commit
pre-commit install
```

## CI/CD

- **CI**: Linting, unit tests (3 OS × 3 Python versions), security scan on push
- **CD**: Auto-build executables on version tags

## Logs

Logs are stored at `~/.tts-vmic-bridge/logs/`:
- `app.log` - Application debug logs
- `speech_YYYYMM.jsonl` - Speech event logs (JSONL format)

## License

MIT
