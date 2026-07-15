import io
import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

import aiohttp
import pyttsx3

from src.utils.logger import SpeechLogger

logger = SpeechLogger()

GOOGLE_TRANSLATE_TTS_URL = "https://translate.google.com/translate_tts"
GOOGLE_TTS_VOICES = [
    "en-US-Standard-A",
    "en-US-Standard-B",
    "en-US-Standard-C",
    "en-US-Standard-D",
    "en-US-Standard-E",
    "en-US-Standard-F",
    "en-US-Standard-G",
    "en-US-Standard-H",
    "en-US-Standard-I",
    "en-US-Standard-J",
    "en-US-Neural2-A",
    "en-US-Neural2-B",
    "en-US-Neural2-C",
    "en-US-Neural2-D",
    "en-US-Neural2-E",
    "en-US-Neural2-F",
    "en-US-Neural2-G",
    "en-US-Neural2-H",
    "en-US-Neural2-I",
    "en-US-Neural2-J",
]


class TTSResult:
    def __init__(self, audio_data: bytes, sample_rate: int = 24000, format: str = "wav"):
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.format = format


class BaseTTSEngine(ABC):
    @abstractmethod
    async def synthesize(
        self, text: str, voice: str = "en-US-Standard-A", rate: float = 1.0, pitch: float = 0.0
    ) -> TTSResult: ...

    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def available_voices(self) -> List[str]: ...


class GoogleTranslateTTSEngine(BaseTTSEngine):
    def __init__(self):
        self._voices = ["en-US-Standard-A", "en-US-Standard-B", "en-US-Standard-C"]

    @property
    def name(self) -> str:
        return "google_translate"

    def available_voices(self) -> List[str]:
        return self._voices

    async def synthesize(
        self, text: str, voice: str = "en-US-Standard-A", rate: float = 1.0, pitch: float = 0.0
    ) -> TTSResult:
        params = {
            "ie": "UTF-8",
            "q": text,
            "tl": "en",
            "client": "tw-ob",
            "ttsspeed": str(max(0.2, min(2.0, rate))),
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://translate.google.com/",
        }
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession() as session:
            async with session.get(
                GOOGLE_TRANSLATE_TTS_URL, params=params, headers=headers, timeout=timeout
            ) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Google Translate TTS returned HTTP {resp.status}")
                mp3_data = await resp.read()

        wav_data = self._convert_mp3_to_wav(mp3_data)
        return TTSResult(audio_data=wav_data, sample_rate=24000, format="wav")

    def _convert_mp3_to_wav(self, mp3_data: bytes) -> bytes:
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_mp3(io.BytesIO(mp3_data))
            buf = io.BytesIO()
            audio.export(buf, format="wav")
            return buf.getvalue()
        except ImportError:
            return self._simple_convert(mp3_data)

    def _simple_convert(self, mp3_data: bytes) -> bytes:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(mp3_data)
            mp3_path = tmp.name
        wav_path = mp3_path.replace(".mp3", ".wav")
        try:
            import subprocess

            subprocess.run(
                ["ffmpeg", "-y", "-i", mp3_path, wav_path], capture_output=True, timeout=30
            )
            with open(wav_path, "rb") as f:
                return f.read()
        except Exception:
            raise RuntimeError("Cannot convert MP3 to WAV. Install ffmpeg or pydub.")
        finally:
            for p in [mp3_path, wav_path]:
                try:
                    os.unlink(p)
                except Exception:
                    pass


class OfflineTTSEngine(BaseTTSEngine):
    def __init__(self):
        try:
            engine = pyttsx3.init()
            all_voices = engine.getProperty("voices")
            self._voices = [
                v.name
                for v in all_voices
                if v.languages
                and ("english" in v.name.lower() or v.languages[0].lower().startswith("en"))
            ]
            engine.stop()
            del engine
        except Exception:
            self._voices = []
        if not self._voices:
            self._voices = ["default"]

    @property
    def name(self) -> str:
        return "offline"

    def available_voices(self) -> List[str]:
        return self._voices

    async def synthesize(
        self, text: str, voice: str = "en-US-Standard-A", rate: float = 1.0, pitch: float = 0.0
    ) -> TTSResult:
        import sys

        com_init = False
        if sys.platform == "win32":
            try:
                import comtypes

                comtypes.CoInitialize()
                com_init = True
            except Exception:
                pass

        engine = pyttsx3.init()
        try:
            engine.setProperty("rate", int(engine.getProperty("rate") * rate))
            for v in engine.getProperty("voices"):
                if voice.lower() in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()
            with open(tmp_path, "rb") as f:
                data = f.read()
            return TTSResult(audio_data=data, sample_rate=22050, format="wav")
        finally:
            try:
                engine.stop()
            except Exception:
                pass
            del engine
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            if com_init:
                try:
                    comtypes.CoUninitialize()
                except Exception:
                    pass


class GoogleCloudTTSEngine(BaseTTSEngine):
    def __init__(self, credentials_path: str = ""):
        self._creds_path = credentials_path
        self._client = None
        self._voices = GOOGLE_TTS_VOICES

    @property
    def name(self) -> str:
        return "google_cloud"

    def available_voices(self) -> List[str]:
        return self._voices

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from google.cloud import texttospeech

            if self._creds_path and Path(self._creds_path).exists():
                self._client = texttospeech.TextToSpeechClient.from_service_account_file(
                    self._creds_path
                )
            else:
                self._client = texttospeech.TextToSpeechClient()
            return self._client
        except ImportError:
            raise RuntimeError(
                "google-cloud-texttospeech not installed. "
                "Run: pip install google-cloud-texttospeech"
            )

    async def synthesize(
        self, text: str, voice: str = "en-US-Standard-A", rate: float = 1.0, pitch: float = 0.0
    ) -> TTSResult:
        client = self._get_client()
        voice_name = voice if voice in self._voices else "en-US-Standard-A"
        response = client.synthesize_speech(
            input={"text": text},
            voice={"language_code": "en-US", "name": voice_name},
            audio_config={
                "audio_encoding": 1,
                "speaking_rate": rate,
                "pitch": pitch,
            },
        )
        return TTSResult(audio_data=response.audio_content, sample_rate=24000, format="wav")


def create_tts_engine(
    engine_type: str = "google_translate", credentials_path: str = ""
) -> BaseTTSEngine:
    engines = {
        "google_translate": GoogleTranslateTTSEngine,
        "google_cloud": lambda: GoogleCloudTTSEngine(credentials_path),
        "offline": OfflineTTSEngine,
    }
    factory = engines.get(engine_type)
    if factory is None:
        logger.warning(f"Unknown engine '{engine_type}', falling back to google_translate")
        return GoogleTranslateTTSEngine()
    return factory()
