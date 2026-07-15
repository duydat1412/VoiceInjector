import threading
from typing import Optional, Callable

import numpy as np
import sounddevice as sd

from src.utils.logger import SpeechLogger

logger = SpeechLogger()


class AudioRouter:
    def __init__(self):
        self._stream: Optional[sd.OutputStream] = None
        self._is_playing = False
        self._stop_flag = threading.Event()
        self._on_finished: Optional[Callable] = None
        self._lock = threading.Lock()

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def set_on_finished(self, callback: Callable):
        self._on_finished = callback

    def play_wav(self, wav_data: bytes, device_index: Optional[int] = None):
        import wave
        import io

        with self._lock:
            self.stop()
            self._stop_flag.clear()

        with io.BytesIO(wav_data) as buf:
            with wave.open(buf, "rb") as wf:
                frames = wf.getnframes()
                sample_rate = wf.getframerate()
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                raw = wf.readframes(frames)

        dtype_map = {1: np.int16, 2: np.int16, 4: np.float32}
        dtype = dtype_map.get(sampwidth, np.int16)
        audio = np.frombuffer(raw, dtype=dtype)

        if n_channels > 1:
            audio = audio.reshape(-1, n_channels)

        self._is_playing = True

        def callback(outdata, frames, time_info, status):
            if self._stop_flag.is_set():
                raise sd.CallbackStop
            if len(audio) == 0:
                raise sd.CallbackStop
            n = min(len(audio), frames)
            outdata[:n] = audio[:n]
            if n < frames:
                outdata[n:] = 0
                raise sd.CallbackStop
            nonlocal audio
            audio = audio[n:]

        try:
            self._stream = sd.OutputStream(
                samplerate=sample_rate,
                device=device_index,
                channels=n_channels if n_channels <= 2 else 2,
                callback=callback,
                blocksize=1024,
                dtype=dtype,
                finished_callback=self._on_playback_finished,
            )
            self._stream.start()
        except Exception as e:
            self._is_playing = False
            logger.error(f"Audio playback failed: {e}")
            raise

    def _on_playback_finished(self):
        self._is_playing = False
        if self._on_finished:
            self._on_finished()

    def stop(self):
        self._stop_flag.set()
        with self._lock:
            if self._stream:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception:
                    pass
                self._stream = None
            self._is_playing = False
