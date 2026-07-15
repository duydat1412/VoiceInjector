import sys
import asyncio

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor, QFont

from src.ui.main_window import MainWindow
from src.utils.logger import SpeechLogger

logger = SpeechLogger()

GLOBAL_STYLE = """
QToolTip {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}
QMenu {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px;
}
QMenu::item {
    padding: 4px 20px;
    border-radius: 3px;
}
QMenu::item:selected {
    background-color: #45475a;
}
QMessageBox {
    background-color: #1e1e2e;
}
QMessageBox QLabel {
    color: #cdd6f4;
}
"""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VoiceInjector")
    app.setOrganizationName("VoiceInjector")

    app.setStyleSheet(GLOBAL_STYLE)

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(30, 30, 46))
    palette.setColor(QPalette.WindowText, QColor(205, 214, 244))
    palette.setColor(QPalette.Base, QColor(24, 24, 37))
    palette.setColor(QPalette.AlternateBase, QColor(30, 30, 46))
    palette.setColor(QPalette.ToolTipBase, QColor(49, 50, 68))
    palette.setColor(QPalette.ToolTipText, QColor(205, 214, 244))
    palette.setColor(QPalette.Text, QColor(205, 214, 244))
    palette.setColor(QPalette.Button, QColor(49, 50, 68))
    palette.setColor(QPalette.ButtonText, QColor(205, 214, 244))
    palette.setColor(QPalette.BrightText, QColor(243, 139, 168))
    palette.setColor(QPalette.Link, QColor(203, 166, 247))
    palette.setColor(QPalette.Highlight, QColor(203, 166, 247))
    palette.setColor(QPalette.HighlightedText, QColor(30, 30, 46))
    app.setPalette(palette)

    font = QFont("Segoe UI", 10)
    app.setFont(font)

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
