import io
import threading
import wave
from typing import Optional

import numpy as np
import sounddevice as sd

from src.utils.logger import SpeechLogger

logger = SpeechLogger()


class AudioRouter:
    def __init__(self):
        self._streams = []
        self._is_playing = False
        self._stop_event = threading.Event()

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def play(
        self,
        wav_data: bytes,
        virtual_device: Optional[int] = None,
        speaker_device: Optional[int] = None,
    ):
        """Play WAV to virtual mic and speakers simultaneously. Blocks until done."""
        self.stop()
        self._stop_event.clear()

        audio, sample_rate, channels, dtype = self._parse_wav(wav_data)

        # Collect unique devices to play to
        devices = []
        if virtual_device is not None:
            devices.append(virtual_device)
        if speaker_device is not None and speaker_device != virtual_device:
            devices.append(speaker_device)

        if not devices:
            logger.warning("No output devices selected")
            return

        self._is_playing = True
        done_event = threading.Event()
        remaining = [len(devices)]
        lock = threading.Lock()

        def on_stream_done():
            with lock:
                remaining[0] -= 1
                if remaining[0] <= 0:
                    self._is_playing = False
                    done_event.set()

        for dev_idx in devices:
            audio_copy = audio.copy()
            pos = [0]

            def make_callback(aud, p):
                def callback(outdata, frames, time_info, status):
                    if self._stop_event.is_set():
                        raise sd.CallbackStop
                    n = min(len(aud) - p[0], frames)
                    if n > 0:
                        outdata[:n] = aud[p[0] : p[0] + n]
                        p[0] += n
                    if n < frames:
                        outdata[n:] = 0
                        raise sd.CallbackStop

                return callback

            try:
                stream = sd.OutputStream(
                    samplerate=sample_rate,
                    device=dev_idx,
                    channels=channels,
                    callback=make_callback(audio_copy, pos),
                    blocksize=1024,
                    dtype=dtype,
                    finished_callback=on_stream_done,
                )
                self._streams.append(stream)
                stream.start()
            except Exception as e:
                logger.error(f"Failed to play on device {dev_idx}: {e}")
                on_stream_done()

        done_event.wait()

    def _parse_wav(self, wav_data: bytes):
        with io.BytesIO(wav_data) as buf:
            with wave.open(buf, "rb") as wf:
                sample_rate = wf.getframerate()
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                raw = wf.readframes(wf.getnframes())

        dtype_map = {1: np.int8, 2: np.int16, 4: np.float32}
        dtype = dtype_map.get(sampwidth, np.int16)
        audio = np.frombuffer(raw, dtype=dtype).copy()

        if n_channels > 1:
            audio = audio.reshape(-1, n_channels)
        else:
            audio = audio.reshape(-1, 1)

        channels = min(n_channels, 2)
        return audio, sample_rate, channels, dtype

    def stop(self):
        self._stop_event.set()
        for stream in self._streams:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass
        self._streams.clear()
        self._is_playing = False
