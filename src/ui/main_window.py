import asyncio
from typing import Optional

from PySide6.QtCore import QTimer, Signal, QObject, Qt
from PySide6.QtGui import QFont, QIcon, QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QComboBox, QLabel, QSlider, QProgressBar,
    QListWidget, QListWidgetItem, QMessageBox, QFileDialog, QMenu,
    QStatusBar, QGroupBox, QCheckBox, QSpinBox, QDialog, QFormLayout,
    QLineEdit, QDialogButtonBox, QFrame,
)

from src.config.config_manager import ConfigManager
from src.utils.logger import SpeechLogger
from src.utils.device_utils import list_virtual_output_devices, list_output_devices
from src.core.tts_engine import create_tts_engine, BaseTTSEngine
from src.core.audio_router import AudioRouter
from src.core.cache_manager import CacheManager
from src.core.queue_manager import QueueManager, QueueState

logger = SpeechLogger()


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
        self.setMinimumWidth(450)
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QFormLayout(self)
        self._creds_path = QLineEdit()
        self._creds_btn = QPushButton("Browse...")
        creds_row = QHBoxLayout()
        creds_row.addWidget(self._creds_path)
        creds_row.addWidget(self._creds_btn)
        self._creds_btn.clicked.connect(self._browse_creds)
        layout.addRow("Google Cloud Credentials:", creds_row)
        self._max_cache = QSpinBox()
        self._max_cache.setRange(50, 2000)
        self._max_cache.setSuffix(" MB")
        layout.addRow("Max Cache Size:", self._max_cache)
        self._dark_mode = QCheckBox("Enable Dark Mode")
        layout.addRow("Appearance:", self._dark_mode)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
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
            self._tts_engine = create_tts_engine(
                cfg.tts_engine, cfg.gcloud_credentials_path
            )
        except Exception as e:
            logger.error(f"Failed to init TTS engine: {e}")
            self._tts_engine = create_tts_engine("google_translate")

    def _setup_ui(self):
        self.setWindowTitle("TTS Virtual Mic Bridge")
        self.setMinimumSize(500, 600)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(8)

        # Top toolbar area
        toolbar = QHBoxLayout()
        self._device_combo = QComboBox()
        self._device_combo.setMinimumWidth(220)
        self._refresh_btn = QPushButton("🔄")
        self._refresh_btn.setToolTip("Refresh audio devices")
        self._refresh_btn.setFixedWidth(32)
        toolbar.addWidget(QLabel("Virtual Mic:"))
        toolbar.addWidget(self._device_combo, 1)
        toolbar.addWidget(self._refresh_btn)
        layout.addLayout(toolbar)

        # Voice and speed row
        controls = QHBoxLayout()
        self._voice_combo = QComboBox()
        self._voice_combo.setMinimumWidth(160)
        voices = self._tts_engine.available_voices() if self._tts_engine else []
        self._voice_combo.addItems(voices)
        controls.addWidget(QLabel("Voice:"))
        controls.addWidget(self._voice_combo)
        controls.addWidget(QLabel("Speed:"))
        self._speed_slider = QSlider(Qt.Horizontal)
        self._speed_slider.setRange(50, 200)
        self._speed_slider.setValue(100)
        self._speed_slider.setToolTip("Speech rate: 50% to 200%")
        controls.addWidget(self._speed_slider)
        self._speed_label = QLabel("1.0x")
        self._speed_label.setFixedWidth(40)
        controls.addWidget(self._speed_label)
        layout.addLayout(controls)

        # Engine selector
        engine_row = QHBoxLayout()
        self._engine_combo = QComboBox()
        self._engine_combo.addItems(["Google Translate (Free)", "Google Cloud (High Quality)", "Offline (pyttsx3)"])
        self._engine_combo.setCurrentIndex(0)
        engine_row.addWidget(QLabel("TTS Engine:"))
        engine_row.addWidget(self._engine_combo, 1)
        self._settings_btn = QPushButton("⚙️ Settings")
        self._settings_btn.setFixedWidth(100)
        engine_row.addWidget(self._settings_btn)
        layout.addLayout(engine_row)

        # Text input
        self._text_edit = QTextEdit()
        self._text_edit.setPlaceholderText(
            "Paste your English questions here...\n"
            "One question per line for batch processing."
        )
        self._text_edit.setMinimumHeight(150)
        self._text_edit.setAcceptRichText(False)
        layout.addWidget(QLabel("Text to speak:"))
        layout.addWidget(self._text_edit)

        # Action buttons
        btn_row = QHBoxLayout()
        self._speak_btn = QPushButton("▶ Speak All")
        self._speak_btn.setMinimumHeight(36)
        self._stop_btn = QPushButton("⏹ Stop")
        self._stop_btn.setMinimumHeight(36)
        self._stop_btn.setEnabled(False)
        self._skip_btn = QPushButton("⏭ Skip")
        self._skip_btn.setMinimumHeight(36)
        self._skip_btn.setEnabled(False)
        self._clear_btn = QPushButton("🗑 Clear")
        self._clear_btn.setMinimumHeight(36)
        btn_row.addWidget(self._speak_btn)
        btn_row.addWidget(self._stop_btn)
        btn_row.addWidget(self._skip_btn)
        btn_row.addWidget(self._clear_btn)
        layout.addLayout(btn_row)

        # Status and queue
        self._status_label = QLabel("Status: Idle")
        self._status_label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        layout.addWidget(self._status_label)

        self._queue_list = QListWidget()
        self._queue_list.setMaximumHeight(120)
        layout.addWidget(QLabel("Queue:"))
        layout.addWidget(self._queue_list)

        # Progress
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # Status bar
        self.statusBar().showMessage("Ready")

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Return"), self, self._on_speak).setContext(Qt.ApplicationShortcut)
        QShortcut(QKeySequence("Escape"), self, self._on_stop).setContext(Qt.ApplicationShortcut)
        QShortcut(QKeySequence("Ctrl+Return"), self, self._on_speak_queue).setContext(Qt.ApplicationShortcut)

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
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        self._queue_manager.clear()
        self._queue_manager.add_items(lines)
        self._update_queue_display()
        self._start_queue()

    def _on_stop(self):
        self._audio_router.stop()
        self._queue_manager.clear()
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
        asyncio.ensure_future(self._process_queue())

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
            self._audio_router.play_wav(wav_data, device_idx)
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
        self._status_label.setText(
            f"Status: Speaking ({index + 1}/{total})"
        )
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
        self._status_label.setText("Status: Idle")

    def _update_queue_display(self):
        self._queue_list.clear()
        for item in self._queue_manager.items:
            prefix = "⏭ " if item.skipped else ""
            display = f"{prefix}{item.text[:60]}{'...' if len(item.text) > 60 else ''}"
            QListWidgetItem(display, self._queue_list)

    def closeEvent(self, event):
        self._audio_router.stop()
        cfg = self._config.config
        geo = self.geometry()
        self._config.update(
            window_x=geo.x(), window_y=geo.y(),
            window_width=geo.width(), window_height=geo.height(),
            default_device=self._device_combo.currentText(),
            default_voice=self._voice_combo.currentText(),
            speech_rate=self._speed_slider.value() / 100.0,
        )
        event.accept()
