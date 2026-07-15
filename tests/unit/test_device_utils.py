from unittest.mock import patch

from src.utils.device_utils import (
    list_virtual_output_devices,
    get_device_by_name,
)


class TestDeviceUtils:
    @patch("src.utils.device_utils.sd.query_devices")
    def test_list_virtual_output_devices(self, mock_query):
        mock_query.return_value = [
            {"name": "CABLE Output (VB-Audio Virtual Cable)", "max_output_channels": 2,
             "max_input_channels": 0, "default_samplerate": 48000, "hostapi": 0, "index": 0},
            {"name": "Speakers (Realtek Audio)", "max_output_channels": 2,
             "max_input_channels": 0, "default_samplerate": 48000, "hostapi": 0, "index": 1},
            {"name": "BlackHole 16ch", "max_output_channels": 16,
             "max_input_channels": 16, "default_samplerate": 48000, "hostapi": 0, "index": 2},
        ]
        virtual = list_virtual_output_devices()
        assert len(virtual) == 2
        assert "CABLE" in virtual[0]["name"]
        assert "BlackHole" in virtual[1]["name"]

    @patch("src.utils.device_utils.sd.query_devices")
    def test_get_device_by_name(self, mock_query):
        mock_query.return_value = [
            {"name": "CABLE Output", "max_output_channels": 2,
             "max_input_channels": 0, "default_samplerate": 48000, "hostapi": 0, "index": 0},
        ]
        dev = get_device_by_name("CABLE")
        assert dev is not None
        assert dev["name"] == "CABLE Output"

    @patch("src.utils.device_utils.sd.query_devices")
    def test_get_device_by_name_not_found(self, mock_query):
        mock_query.return_value = []
        dev = get_device_by_name("Nonexistent")
        assert dev is None
