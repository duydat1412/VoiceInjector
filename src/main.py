import sys
import asyncio

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

from src.ui.main_window import MainWindow
from src.config.config_manager import ConfigManager
from src.utils.logger import SpeechLogger

logger = SpeechLogger()


def apply_theme(app: QApplication, dark: bool):
    if dark:
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        app.setPalette(palette)
    else:
        app.setPalette(app.style().standardPalette())


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TTS Virtual Mic Bridge")
    app.setOrganizationName("TTSVmicBridge")

    config = ConfigManager()
    apply_theme(app, config.config.dark_mode)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    except Exception as e:
        logger.warning(f"Failed to set up asyncio event loop: {e}")

    window = MainWindow()
    window.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        pass


if __name__ == "__main__":
    main()
