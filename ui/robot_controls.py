from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QApplication
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


CONTROLS_STYLE = """
    QWidget {
        background: #1c1c1e;
        border: 1px solid #3a3a3c;
        border-radius: 10px;
    }
    QPushButton {
        color: #f5f5f7;
        background: transparent;
        border: none;
        border-radius: 5px;
        padding: 8px 16px;
        font-size: 12px;
        text-align: left;
    }
    QPushButton:hover {
        background: #2c2c2e;
    }
    QPushButton:pressed {
        background: #3a3a3c;
    }
"""


class RobotControls(QWidget):
    pause_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()

    def __init__(self, bubble):
        super().__init__(bubble.parent())
        self.bubble = bubble
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._paused = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self._btn_pause = QPushButton("⏸  Pausar")
        self._btn_stop = QPushButton("⏹  Detener")

        self._btn_pause.setStyleSheet(CONTROLS_STYLE)
        self._btn_stop.setStyleSheet(CONTROLS_STYLE)

        self._btn_pause.clicked.connect(self._on_pause)
        self._btn_stop.clicked.connect(self.stop_clicked)

        layout.addWidget(self._btn_pause)
        layout.addWidget(self._btn_stop)
        self.setStyleSheet(CONTROLS_STYLE)

        self.adjustSize()

    def _on_pause(self):
        self._paused = not self._paused
        if self._paused:
            self._btn_pause.setText("▶  Reanudar")
        else:
            self._btn_pause.setText("⏸  Pausar")
        self.pause_clicked.emit()

    def set_paused(self, paused: bool):
        self._paused = paused
        self._btn_pause.setText("▶  Reanudar" if paused else "⏸  Pausar")

    def reposition(self):
        bubble_geo = self.bubble.frameGeometry()
        screen = QApplication.primaryScreen().geometry()
        w = self.width()
        margin = 8

        if bubble_geo.right() + w + margin < screen.right():
            x = bubble_geo.right() + margin
        else:
            x = bubble_geo.left() - w - margin

        y = bubble_geo.top()
        self.move(x, y)

    def showEvent(self, event):
        super().showEvent(event)
        self.reposition()
