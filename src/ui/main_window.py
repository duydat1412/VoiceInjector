import asyncio
from typing import Optional

from PySide6.QtCore import Signal, QObject, Qt, QThread
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QComboBox,
    QLabel,
    QSlider,
    QProgressBar,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QFileDialog,
    QCheckBox,
    QSpinBox,
    QDialog,
    QFormLayout,
    QLineEdit,
    QFrame,
)

from src.config.config_manager import ConfigManager
from src.utils.logger import SpeechLogger
from src.utils.device_utils import list_virtual_output_devices, list_output_devices
from src.core.tts_engine import create_tts_engine, BaseTTSEngine
from src.core.audio_router import AudioRouter
from src.core.cache_manager import CacheManager
from src.core.queue_manager import QueueManager, QueueState

logger = SpeechLogger()

STYLE = """
QMainWindow {
    background-color: #1e1e2e;
}
QLabel {
    color: #cdd6f4;
    font-size: 13px;
}
QLabel#titleLabel {
    color: #cba6f7;
    font-size: 16px;
    font-weight: bold;
    padding: 4px 0;
}
QLabel#statusIndicator {
    font-size: 13px;
    padding: 6px 12px;
    border-radius: 4px;
    background-color: #313244;
    color: #a6adc8;
}
QLabel#statusIndicator[active="true"] {
    background-color: #1e1e3a;
    color: #a6e3a1;
}
QTextEdit {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px;
    font-size: 13px;
    selection-background-color: #585b70;
}
QTextEdit:focus {
    border: 1px solid #cba6f7;
}
QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 5px 10px;
    min-height: 24px;
    font-size: 12px;
}
QComboBox:hover {
    border: 1px solid #585b70;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #cdd6f4;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    selection-background-color: #45475a;
    border: 1px solid #585b70;
    border-radius: 4px;
}
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 12px;
    min-height: 20px;
}
QPushButton:hover {
    background-color: #45475a;
    border: 1px solid #585b70;
}
QPushButton:pressed {
    background-color: #585b70;
}
QPushButton:disabled {
    background-color: #1e1e2e;
    color: #585b70;
    border: 1px solid #313244;
}
QPushButton#speakBtn {
    background-color: #a6e3a1;
    color: #1e1e2e;
    border: none;
    font-weight: bold;
    font-size: 13px;
}
QPushButton#speakBtn:hover {
    background-color: #94e2d5;
}
QPushButton#speakBtn:disabled {
    background-color: #45475a;
    color: #585b70;
}
QPushButton#stopBtn {
    background-color: #f38ba8;
    color: #1e1e2e;
    border: none;
    font-weight: bold;
    font-size: 13px;
}
QPushButton#stopBtn:hover {
    background-color: #eba0ac;
}
QPushButton#stopBtn:disabled {
    background-color: #45475a;
    color: #585b70;
}
QPushButton#settingsBtn {
    background-color: #45475a;
    padding: 6px 12px;
}
QPushButton#settingsBtn:hover {
    background-color: #585b70;
}
QPushButton#iconBtn {
    background-color: #313244;
    border: 1px solid #45475a;
    padding: 4px;
    min-width: 28px;
    max-width: 28px;
    min-height: 24px;
    max-height: 24px;
    font-size: 14px;
}
QPushButton#iconBtn:hover {
    background-color: #45475a;
}
QSlider::groove:horizontal {
    height: 4px;
    background: #45475a;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #cba6f7;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
QSlider::handle:horizontal:hover {
    background: #f5c2e7;
}
QProgressBar {
    background-color: #313244;
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background-color: #cba6f7;
    border-radius: 3px;
}
QListWidget {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 4px;
    font-size: 12px;
    outline: none;
}
QListWidget::item {
    padding: 4px 8px;
    border-radius: 3px;
}
QListWidget::item:selected {
    background-color: #45475a;
}
QListWidget::item:alternate {
    background-color: #1e1e2e;
}
QScrollBar:vertical {
    background: #181825;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #45475a;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #585b70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: #181825;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #45475a;
    min-width: 20px;
    border-radius: 4px;
}
QStatusBar {
    background-color: #181825;
    color: #a6adc8;
    font-size: 11px;
    border-top: 1px solid #313244;
}
QFrame#separator {
    background-color: #313244;
    max-height: 1px;
}
"""


class AsyncWorker(QObject):
    finished = Signal()
    error = Signal(str)

    def __init__(self, coro):
        super().__init__()
        self._coro = coro

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._coro)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class SettingsDialog(QDialog):
    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("Settings")
        self.setMinimumWidth(480)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; }
            QLabel { color: #cdd6f4; }
            QLineEdit {
                background-color: #181825; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 4px;
                padding: 5px 8px; font-size: 12px;
            }
            QLineEdit:focus { border: 1px solid #cba6f7; }
            QSpinBox {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 4px;
                padding: 5px; font-size: 12px;
            }
            QCheckBox { color: #cdd6f4; spacing: 8px; }
            QCheckBox::indicator {
                width: 16px; height: 16px;
                border: 1px solid #45475a; border-radius: 3px;
                background-color: #181825;
            }
            QCheckBox::indicator:checked {
                background-color: #a6e3a1; border-color: #a6e3a1;
            }
            QPushButton {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 4px;
                padding: 6px 16px; font-size: 12px;
            }
            QPushButton:hover { background-color: #45475a; }
            QPushButton#okBtn {
                background-color: #a6e3a1; color: #1e1e2e;
                border: none; font-weight: bold;
            }
            QPushButton#okBtn:hover { background-color: #94e2d5; }
            QPushButton#cancelBtn {
                background-color: #f38ba8; color: #1e1e2e; border: none;
            }
            QPushButton#cancelBtn:hover { background-color: #eba0ac; }
        """)
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        self._creds_path = QLineEdit()
        self._creds_path.setPlaceholderText("Path to service-account.json")
        self._creds_btn = QPushButton("Browse...")
        self._creds_btn.setFixedWidth(80)
        creds_row = QHBoxLayout()
        creds_row.setSpacing(8)
        creds_row.addWidget(self._creds_path, 1)
        creds_row.addWidget(self._creds_btn)
        self._creds_btn.clicked.connect(self._browse_creds)
        layout.addRow("Google Cloud Credentials:", creds_row)

        self._max_cache = QSpinBox()
        self._max_cache.setRange(50, 2000)
        self._max_cache.setSuffix(" MB")
        layout.addRow("Max Cache Size:", self._max_cache)

        self._dark_mode = QCheckBox("Enable Dark Mode")
        self._dark_mode.setChecked(True)
        self._dark_mode.setEnabled(False)
        layout.addRow("Appearance:", self._dark_mode)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addStretch()
        ok_btn = QPushButton("Save")
        ok_btn.setObjectName("okBtn")
        ok_btn.setFixedWidth(80)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)

    def _browse_creds(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Google Cloud Credentials JSON", "", "JSON Files (*.json)"
        )
        if path:
            self._creds_path.setText(path)

    def _load_values(self):
        cfg = self._config.config
        self._creds_path.setText(cfg.gcloud_credentials_path)
        self._max_cache.setValue(cfg.max_cache_size_mb)
        self._dark_mode.setChecked(cfg.dark_mode)

    def _save(self):
        self._config.update(
            gcloud_credentials_path=self._creds_path.text().strip(),
            max_cache_size_mb=self._max_cache.value(),
            dark_mode=self._dark_mode.isChecked(),
        )
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._config = ConfigManager()
        self._cache = CacheManager()
        self._audio_router = AudioRouter()
        self._queue_manager = QueueManager()
        self._tts_engine: Optional[BaseTTSEngine] = None
        self._worker_thread = None
        self._init_engine()
        self._setup_ui()
        self._setup_shortcuts()
        self._load_settings()
        self._refresh_devices()
        self._connect_signals()

    def _init_engine(self):
        cfg = self._config.config
        try:
            self._tts_engine = create_tts_engine(cfg.tts_engine, cfg.gcloud_credentials_path)
        except Exception as e:
            logger.error(f"Failed to init TTS engine: {e}")
            self._tts_engine = create_tts_engine("google_translate")

    def _setup_ui(self):
        self.setWindowTitle("VoiceInjector")
        self.setMinimumSize(520, 640)
        self.setStyleSheet(STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(16, 12, 16, 12)

        # Title
        title = QLabel("VoiceInjector")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        subtitle = QLabel("Text-to-Speech into Virtual Microphone")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #6c7086; font-size: 11px; padding-bottom: 4px;")
        main_layout.addWidget(subtitle)

        # Separator
        sep1 = QFrame()
        sep1.setObjectName("separator")
        sep1.setFrameShape(QFrame.HLine)
        main_layout.addWidget(sep1)

        # Device row
        device_row = QHBoxLayout()
        device_row.setSpacing(8)
        device_label = QLabel("Microphone")
        device_label.setStyleSheet("color: #a6adc8; font-size: 11px; font-weight: bold;")
        self._device_combo = QComboBox()
        self._device_combo.setMinimumWidth(200)
        self._refresh_btn = QPushButton("\u21bb")
        self._refresh_btn.setObjectName("iconBtn")
        self._refresh_btn.setToolTip("Refresh audio devices")
        device_row.addWidget(device_label)
        device_row.addWidget(self._device_combo, 1)
        device_row.addWidget(self._refresh_btn)
        main_layout.addLayout(device_row)

        # Controls row
        controls = QHBoxLayout()
        controls.setSpacing(12)

        voice_col = QVBoxLayout()
        voice_col.setSpacing(4)
        voice_label = QLabel("Voice")
        voice_label.setStyleSheet("color: #a6adc8; font-size: 11px; font-weight: bold;")
        self._voice_combo = QComboBox()
        self._voice_combo.setMinimumWidth(160)
        voices = self._tts_engine.available_voices() if self._tts_engine else []
        self._voice_combo.addItems(voices)
        voice_col.addWidget(voice_label)
        voice_col.addWidget(self._voice_combo)

        speed_col = QVBoxLayout()
        speed_col.setSpacing(4)
        speed_header = QHBoxLayout()
        speed_label = QLabel("Speed")
        speed_label.setStyleSheet("color: #a6adc8; font-size: 11px; font-weight: bold;")
        self._speed_label = QLabel("1.0x")
        self._speed_label.setStyleSheet("color: #cba6f7; font-size: 11px; font-weight: bold;")
        self._speed_label.setFixedWidth(36)
        self._speed_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        speed_header.addWidget(speed_label)
        speed_header.addStretch()
        speed_header.addWidget(self._speed_label)
        self._speed_slider = QSlider(Qt.Horizontal)
        self._speed_slider.setRange(50, 200)
        self._speed_slider.setValue(100)
        self._speed_slider.setToolTip("Speech rate: 50% to 200%")
        speed_col.addLayout(speed_header)
        speed_col.addWidget(self._speed_slider)

        controls.addLayout(voice_col, 1)
        controls.addLayout(speed_col, 1)
        main_layout.addLayout(controls)

        # Engine row
        engine_row = QHBoxLayout()
        engine_row.setSpacing(8)
        engine_label = QLabel("Engine")
        engine_label.setStyleSheet("color: #a6adc8; font-size: 11px; font-weight: bold;")
        self._engine_combo = QComboBox()
        self._engine_combo.addItems(
            ["Google Translate (Free)", "Google Cloud (High Quality)", "Offline (pyttsx3)"]
        )
        self._engine_combo.setCurrentIndex(0)
        self._settings_btn = QPushButton("Settings")
        self._settings_btn.setObjectName("settingsBtn")
        self._settings_btn.setFixedWidth(72)
        engine_row.addWidget(engine_label)
        engine_row.addWidget(self._engine_combo, 1)
        engine_row.addWidget(self._settings_btn)
        main_layout.addLayout(engine_row)

        # Separator
        sep2 = QFrame()
        sep2.setObjectName("separator")
        sep2.setFrameShape(QFrame.HLine)
        main_layout.addWidget(sep2)

        # Text input
        text_label = QLabel("Text to speak")
        text_label.setStyleSheet("color: #a6adc8; font-size: 11px; font-weight: bold;")
        main_layout.addWidget(text_label)
        self._text_edit = QTextEdit()
        self._text_edit.setPlaceholderText(
            "Paste your English questions here...\n" "One question per line for batch processing."
        )
        self._text_edit.setMinimumHeight(140)
        self._text_edit.setAcceptRichText(False)
        main_layout.addWidget(self._text_edit)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self._speak_btn = QPushButton("Speak All")
        self._speak_btn.setObjectName("speakBtn")
        self._speak_btn.setMinimumHeight(34)
        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setObjectName("stopBtn")
        self._stop_btn.setMinimumHeight(34)
        self._stop_btn.setEnabled(False)
        self._skip_btn = QPushButton("Skip")
        self._skip_btn.setMinimumHeight(34)
        self._skip_btn.setEnabled(False)
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setMinimumHeight(34)
        btn_row.addWidget(self._speak_btn)
        btn_row.addWidget(self._stop_btn)
        btn_row.addWidget(self._skip_btn)
        btn_row.addWidget(self._clear_btn)
        main_layout.addLayout(btn_row)

        # Status
        self._status_label = QLabel("Idle")
        self._status_label.setObjectName("statusIndicator")
        self._status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self._status_label)

        # Progress
        self._progress = QProgressBar()
        self._progress.setFixedHeight(6)
        self._progress.setVisible(False)
        main_layout.addWidget(self._progress)

        # Queue
        queue_header = QHBoxLayout()
        queue_label = QLabel("Queue")
        queue_label.setStyleSheet("color: #a6adc8; font-size: 11px; font-weight: bold;")
        self._queue_count = QLabel("0")
        self._queue_count.setStyleSheet("color: #585b70; font-size: 11px;")
        queue_header.addWidget(queue_label)
        queue_header.addStretch()
        queue_header.addWidget(self._queue_count)
        main_layout.addLayout(queue_header)

        self._queue_list = QListWidget()
        self._queue_list.setMaximumHeight(110)
        main_layout.addWidget(self._queue_list)

        # Status bar
        self.statusBar().showMessage("Ready")

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Return"), self, self._on_speak).setContext(Qt.ApplicationShortcut)
        QShortcut(QKeySequence("Escape"), self, self._on_stop).setContext(Qt.ApplicationShortcut)
        ctrl = QShortcut(QKeySequence("Ctrl+Return"), self, self._on_speak)
        ctrl.setContext(Qt.ApplicationShortcut)

    def _load_settings(self):
        cfg = self._config.config
        if cfg.default_device:
            idx = self._device_combo.findText(cfg.default_device, Qt.MatchContains)
            if idx >= 0:
                self._device_combo.setCurrentIndex(idx)
        if cfg.default_voice:
            idx = self._voice_combo.findText(cfg.default_voice)
            if idx >= 0:
                self._voice_combo.setCurrentIndex(idx)
        self._speed_slider.setValue(int(cfg.speech_rate * 100))
        self._on_speed_changed(cfg.speech_rate)
        engine_map = {"google_translate": 0, "google_cloud": 1, "offline": 2}
        self._engine_combo.setCurrentIndex(engine_map.get(cfg.tts_engine, 0))
        if cfg.window_x >= 0 and cfg.window_y >= 0:
            self.move(cfg.window_x, cfg.window_y)
        if cfg.window_width > 0 and cfg.window_height > 0:
            self.resize(cfg.window_width, cfg.window_height)

    def _connect_signals(self):
        self._speak_btn.clicked.connect(self._on_speak)
        self._stop_btn.clicked.connect(self._on_stop)
        self._skip_btn.clicked.connect(self._on_skip)
        self._clear_btn.clicked.connect(self._on_clear)
        self._refresh_btn.clicked.connect(self._refresh_devices)
        self._settings_btn.clicked.connect(self._on_settings)
        self._speed_slider.valueChanged.connect(self._on_speed_changed)
        self._engine_combo.currentIndexChanged.connect(self._on_engine_changed)
        self._audio_router.set_on_finished(self._on_playback_finished)
        self._queue_manager.set_on_state_change(self._on_queue_state_change)
        self._queue_manager.set_on_item_change(self._on_queue_item_change)
        self._queue_manager.set_on_finished(self._on_queue_finished)

    def _refresh_devices(self):
        self._device_combo.clear()
        devices = list_virtual_output_devices()
        if not devices:
            devices = list_output_devices()
        for d in devices:
            label = f"{d['name']} (#{d['index']})"
            self._device_combo.addItem(label, d["index"])
        if self._device_combo.count() == 0:
            self._device_combo.addItem("No output devices found", -1)

    def _on_speed_changed(self, value):
        if isinstance(value, int):
            rate = value / 100.0
        else:
            rate = value
        self._speed_label.setText(f"{rate:.1f}x")

    def _on_engine_changed(self, idx):
        engine_map = {0: "google_translate", 1: "google_cloud", 2: "offline"}
        engine_type = engine_map.get(idx, "google_translate")
        cfg = self._config.config
        try:
            self._tts_engine = create_tts_engine(engine_type, cfg.gcloud_credentials_path)
            self._voice_combo.clear()
            self._voice_combo.addItems(self._tts_engine.available_voices())
            self._config.update(tts_engine=engine_type)
        except Exception as e:
            QMessageBox.warning(self, "Engine Error", f"Failed to switch engine: {e}")

    def _on_settings(self):
        dlg = SettingsDialog(self._config, self)
        if dlg.exec() == QDialog.Accepted:
            self._on_engine_changed(self._engine_combo.currentIndex())
            self.statusBar().showMessage("Settings saved", 3000)

    def _on_speak(self):
        text = self._text_edit.toPlainText().strip()
        if not text:
            self.statusBar().showMessage("No text to speak", 3000)
            return
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        self._queue_manager.clear()
        self._queue_manager.add_items(lines)
        self._update_queue_display()
        self._start_queue()

    def _on_stop(self):
        self._audio_router.stop()
        self._queue_manager.clear()
        if self._worker_thread and self._worker_thread.isRunning():
            self._worker_thread.quit()
            self._worker_thread.wait(2000)
        self._update_queue_display()
        self._set_idle_state()

    def _on_skip(self):
        self._queue_manager.skip_current()
        self._audio_router.stop()

    def _on_clear(self):
        self._text_edit.clear()
        self._queue_manager.clear()
        self._update_queue_display()

    def _start_queue(self):
        self._speak_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._skip_btn.setEnabled(True)
        self._progress.setVisible(True)
        self._status_label.setText("Speaking...")
        self._status_label.setProperty("active", True)
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

        worker = AsyncWorker(self._process_queue())
        thread = QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        worker.error.connect(lambda e: logger.error(f"Queue error: {e}"))
        self._worker_thread = thread
        thread.start()

    async def _process_queue(self):
        async def speak(text):
            await self._do_speak(text)

        await self._queue_manager.process(speak)

    async def _do_speak(self, text: str):
        voice = self._voice_combo.currentText()
        rate = self._speed_slider.value() / 100.0
        device_idx = self._device_combo.currentData()
        if device_idx is None or device_idx < 0:
            device_idx = None

        cached = self._cache.get(text, voice, rate, 0.0)
        if cached:
            wav_data = cached["audio_data"]
        else:
            try:
                result = await self._tts_engine.synthesize(text, voice, rate, 0.0)
                wav_data = result.audio_data
                self._cache.put(text, voice, rate, 0.0, wav_data, result.sample_rate)
            except Exception as e:
                logger.error(f"TTS synthesis failed: {e}")
                self.statusBar().showMessage(f"TTS error: {e}", 5000)
                return

        try:
            self._audio_router.play_wav_blocking(wav_data, device_idx)
            device_name = self._device_combo.currentText()
            logger.log_speech(text, voice, device_name, 0, self._tts_engine.name)
        except Exception as e:
            logger.error(f"Playback failed: {e}")
            self.statusBar().showMessage(f"Playback error: {e}", 5000)

    def _on_playback_finished(self):
        pass

    def _on_queue_state_change(self, state: QueueState):
        pass

    def _on_queue_item_change(self, index: int):
        total = self._queue_manager.total
        self._status_label.setText(f"Speaking {index + 1}/{total}")
        self._progress.setMaximum(total)
        self._progress.setValue(index + 1)

    def _on_queue_finished(self):
        self._set_idle_state()
        self.statusBar().showMessage("Queue completed", 3000)

    def _set_idle_state(self):
        self._speak_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._skip_btn.setEnabled(False)
        self._progress.setVisible(False)
        self._status_label.setText("Idle")
        self._status_label.setProperty("active", False)
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

    def _update_queue_display(self):
        self._queue_list.clear()
        count = 0
        for item in self._queue_manager.items:
            prefix = "[skipped] " if item.skipped else ""
            display = f"{prefix}{item.text[:55]}{'...' if len(item.text) > 55 else ''}"
            QListWidgetItem(display, self._queue_list)
            count += 1
        self._queue_count.setText(str(count))

    def closeEvent(self, event):
        self._audio_router.stop()
        geo = self.geometry()
        self._config.update(
            window_x=geo.x(),
            window_y=geo.y(),
            window_width=geo.width(),
            window_height=geo.height(),
            default_device=self._device_combo.currentText(),
            default_voice=self._voice_combo.currentText(),
            speech_rate=self._speed_slider.value() / 100.0,
        )
        event.accept()
