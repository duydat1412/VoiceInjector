import pytest
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock

from src.core.tts_engine import (
    GoogleTranslateTTSEngine,
    OfflineTTSEngine,
    GoogleCloudTTSEngine,
    create_tts_engine,
    TTSResult,
)


class TestGoogleTranslateTTSEngine:
    @pytest.mark.asyncio
    @patch("src.core.tts_engine.aiohttp.ClientSession")
    @patch("src.core.tts_engine.GoogleTranslateTTSEngine._convert_mp3_to_wav")
    async def test_synthesize_success(self, mock_convert, mock_session):
        mock_convert.return_value = b"fake_wav_data"
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.__aenter__.return_value = mock_resp
        mock_resp.read.return_value = b"fake_mp3_data"

        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_resp
        mock_session.return_value.__aenter__.return_value = mock_session_instance

        engine = GoogleTranslateTTSEngine()
        result = await engine.synthesize("Hello world")
        assert isinstance(result, TTSResult)
        assert result.audio_data == b"fake_wav_data"

    @pytest.mark.asyncio
    @patch("src.core.tts_engine.aiohttp.ClientSession")
    async def test_synthesize_http_error(self, mock_session):
        mock_resp = AsyncMock()
        mock_resp.status = 429
        mock_resp.__aenter__.return_value = mock_resp

        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_resp
        mock_session.return_value.__aenter__.return_value = mock_session_instance

        engine = GoogleTranslateTTSEngine()
        with pytest.raises(RuntimeError, match="Google Translate TTS returned HTTP 429"):
            await engine.synthesize("Hello")

    def test_available_voices(self):
        engine = GoogleTranslateTTSEngine()
        voices = engine.available_voices()
        assert len(voices) > 0
        assert "en-US-Standard-A" in voices

    def test_name(self):
        engine = GoogleTranslateTTSEngine()
        assert engine.name == "google_translate"


class TestGoogleCloudTTSEngine:
    def test_name(self):
        engine = GoogleCloudTTSEngine()
        assert engine.name == "google_cloud"

    def test_available_voices(self):
        engine = GoogleCloudTTSEngine()
        voices = engine.available_voices()
        assert len(voices) > 0
        assert "en-US-Neural2-A" in voices

    @pytest.mark.asyncio
    @patch("src.core.tts_engine.GoogleCloudTTSEngine._get_client")
    async def test_synthesize(self, mock_get_client):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.audio_content = b"fake_wav_data"
        mock_client.synthesize_speech.return_value = mock_response
        mock_get_client.return_value = mock_client

        engine = GoogleCloudTTSEngine()
        result = await engine.synthesize("Hello")
        assert isinstance(result, TTSResult)
        assert result.audio_data == b"fake_wav_data"


class TestOfflineTTSEngine:
    def test_name(self):
        engine = OfflineTTSEngine()
        assert engine.name == "offline"


class TestCreateTTSEngine:
    def test_create_google_translate(self):
        engine = create_tts_engine("google_translate")
        assert engine.name == "google_translate"

    def test_create_offline(self):
        engine = create_tts_engine("offline")
        assert engine.name == "offline"

    def test_create_google_cloud(self):
        engine = create_tts_engine("google_cloud")
        assert engine.name == "google_cloud"

    def test_create_invalid_fallback(self):
        engine = create_tts_engine("invalid_engine")
        assert engine.name == "google_translate"
