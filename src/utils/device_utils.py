from typing import List, Dict, Optional

import sounddevice as sd


def list_audio_devices() -> List[Dict]:
    devices = sd.query_devices()
    result = []
    for idx, dev in enumerate(devices):
        result.append({
            "index": idx,
            "name": dev["name"],
            "max_output_channels": dev["max_output_channels"],
            "max_input_channels": dev["max_input_channels"],
            "default_samplerate": dev["default_samplerate"],
            "hostapi": dev["hostapi"],
        })
    return result


def list_output_devices() -> List[Dict]:
    return [d for d in list_audio_devices() if d["max_output_channels"] > 0]


def list_virtual_output_devices() -> List[Dict]:
    keywords = ["cable", "vb-audio", "voicemeeter", "blackhole", "soundflower",
                "virtual", "loopback", "wavirtual"]
    output_devices = list_output_devices()
    virtual = []
    for d in output_devices:
        name_lower = d["name"].lower()
        if any(kw in name_lower for kw in keywords):
            virtual.append(d)
    return virtual


def get_device_by_name(name: str) -> Optional[Dict]:
    for d in list_audio_devices():
        if name.lower() in d["name"].lower():
            return d
    return None


def get_default_output_device() -> Optional[Dict]:
    try:
        default = sd.query_devices(kind="output")
        return {
            "index": default["index"],
            "name": default["name"],
            "max_output_channels": default["max_output_channels"],
        }
    except Exception:
        return None
