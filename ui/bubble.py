import threading
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QMenu
from PyQt6.QtCore import Qt, QPoint, QRectF, QSize, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QCursor, QPainter, QColor, QPen, QBrush, QPainterPath

BUBBLE_SIZE = 80
RADIUS = 26
PURPLE = "#a78bfa"
MOON_PHASES = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]

MENU_STYLE = """
    QMenu {
        background: #1c1c1e;
        border: 1px solid #3a3a3c;
        border-radius: 10px;
        padding: 4px;
    }
    QMenu::item {
        color: #f5f5f7;
        padding: 7px 16px;
        border-radius: 5px;
        font-size: 12px;
    }
    QMenu::item:selected { background: #2c2c2e; }
    QMenu::separator {
        height: 1px;
        background: #3a3a3c;
        margin: 3px 8px;
    }
"""


class WorkerSignals(QObject):
    result        = pyqtSignal(str)
    error         = pyqtSignal(str)
    paste_ready   = pyqtSignal(str)
    improve_ready = pyqtSignal(str)
    capture_focus = pyqtSignal()


class Bubble(QWidget):
    IDLE       = "idle"
    RECORDING  = "recording"
    PAUSED     = "paused"
    PROCESSING = "processing"
    RESULT     = "result"
    NO_MIC     = "no_mic"

    def __init__(self, recorder, transcriber, cleaner):
        super().__init__()
        self.recorder    = recorder
        self.transcriber = transcriber
        self.cleaner     = cleaner
        self.signals     = WorkerSignals()
        self.signals.result.connect(self._on_result)
        self.signals.error.connect(self._on_error)
        self._drag_pos    = QPoint()
        self._dot_count   = 0
        self._last_text   = ""
        self._incomplete  = False
        self._gen         = 0
        self._pulse_value = 0.0
        self._pulse_dir   = 1
        self._bg          = QColor("#1c1c1e")
        self._border      = QColor("#3a3a3c")
        self._build_ui()
        self._set_state(self.IDLE)

    def _build_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon = QLabel("🌕")
        self._icon.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self._icon.setFont(QFont("Noto Color Emoji", 24))
        self._icon.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._icon.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self._dot_timer = QTimer()
        self._dot_timer.timeout.connect(self._tick_dots)

        self._pulse_timer = QTimer()
        self._pulse_timer.timeout.connect(self._tick_pulse)

        self._pause_timeout = QTimer()
        self._pause_timeout.setSingleShot(True)
        self._pause_timeout.timeout.connect(self._on_pause_timeout)

        self._mic_timer = QTimer()
        self._mic_timer.timeout.connect(self._check_mic)
        self._mic_timer.start(3000)

    def sizeHint(self):
        return QSize(BUBBLE_SIZE + 20, BUBBLE_SIZE + 20)

    def _set_state(self, state):
        self.state = state
        self._dot_timer.stop()
        self._pulse_timer.stop()
        self._pause_timeout.stop()
        self._pulse_value = 0.0
        self._bg = QColor("#1c1c1e")
        self.setFixedSize(BUBBLE_SIZE + 20, BUBBLE_SIZE + 20)

        if state == self.IDLE:
            self._show_moon()
            self._border = QColor("#3a3a3c")
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        elif state == self.RECORDING:
            self._show_recording()
            self._border = QColor(PURPLE)
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self._pulse_timer.start(60)

        elif state == self.PAUSED:
            self._show_recording()
            self._border = QColor("#b8d4fb")
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self._pulse_timer.start(60)
            self._pause_timeout.start(5 * 60 * 1000)

        elif state == self.PROCESSING:
            self._dot_count = 0
            self._show_processing()
            self._border = QColor("#ede0a8")
            self._dot_timer.start(180)

        elif state == self.RESULT:
            self._show_moon()
            self._border = QColor("#5eead4")
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        elif state == self.NO_MIC:
            self._show_no_mic()
            self._border = QColor("#ff6b6b")
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        self.update()

    def _show_moon(self):
        self._icon.setFont(QFont("Noto Color Emoji", 24))
        self._icon.setText("🌕")
        self._icon.setStyleSheet("background: transparent; border: none;")

    def _show_no_mic(self):
        self._icon.setFont(QFont("Noto Color Emoji", 28))
        self._icon.setText("🎤")
        self._icon.setStyleSheet("background: transparent; border: none;")

    def _show_recording(self):
        self._icon.setFont(QFont("Noto Color Emoji", 26))
        self._icon.setText("🎙️")
        self._icon.setStyleSheet("background: transparent; border: none;")

    def _show_processing(self):
        self._icon.setFont(QFont("Noto Color Emoji", 26))
        self._icon.setText(MOON_PHASES[0])
        self._icon.setStyleSheet("background: transparent; border: none;")

    def _tick_dots(self):
        self._dot_count = (self._dot_count + 1) % len(MOON_PHASES)
        self._icon.setText(MOON_PHASES[self._dot_count])

    def _tick_pulse(self):
        self._pulse_value += 0.06 * self._pulse_dir
        if self._pulse_value >= 1.0:
            self._pulse_value = 1.0
            self._pulse_dir = -1
        elif self._pulse_value <= 0.0:
            self._pulse_value = 0.0
            self._pulse_dir = 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        pad = 10
        rect = QRectF(pad, pad, w - pad * 2, h - pad * 2)

        for i in range(8, 0, -1):
            shadow_rect = rect.adjusted(-i * 0.5, i * 0.8, i * 0.5, i * 0.8)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(0, 0, 0, 18 - i)))
            sp = QPainterPath()
            sp.addRoundedRect(shadow_rect, RADIUS, RADIUS)
            painter.drawPath(sp)

        painter.setBrush(QBrush(self._bg))
        if self.state == self.PAUSED:
            alpha = int(130 + 125 * self._pulse_value)
            painter.setPen(QPen(QColor(184, 212, 251, alpha), 4.0))
        elif self.state == self.RECORDING:
            alpha = int(140 + 115 * self._pulse_value)
            painter.setPen(QPen(QColor(167, 139, 250, alpha), 4.0))
        else:
            painter.setPen(QPen(self._border, 4.0))
        path = QPainterPath()
        path.addRoundedRect(rect, RADIUS, RADIUS)
        painter.drawPath(path)


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            pos = event.globalPosition().toPoint() - self._drag_pos
            screen = QApplication.primaryScreen().geometry()
            margin = 16
            x = max(screen.left() + margin, min(pos.x(), screen.right() - self.width() - margin))
            y = max(screen.top() + margin, min(pos.y(), screen.bottom() - self.height() - margin))
            self.move(x, y)

    def contextMenuEvent(self, event):
        self.signals.capture_focus.emit()
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        if self._last_text:
            menu.addAction("↩  Repetir último", self._replay)
        menu.addAction("✨  Mejorar texto", self._improve)
        geo = self.frameGeometry()
        screen = QApplication.primaryScreen().geometry()
        menu_width = 200
        x = geo.right() if geo.right() + menu_width < screen.right() else geo.left() - menu_width
        menu.exec(QPoint(x, geo.top()))

    def _check_mic(self):
        available = self.recorder.is_mic_available()
        if not available and self.state not in (self.RECORDING, self.PAUSED, self.PROCESSING):
            self._set_state(self.NO_MIC)
        elif available and self.state == self.NO_MIC:
            self._set_state(self.IDLE)
        elif not available and self.state in (self.RECORDING, self.PAUSED):
            self._gen += 1
            self.recorder.stop()
            self._set_state(self.NO_MIC)

    def toggle_recording(self):
        if self.state == self.NO_MIC:
            return
        if self.state == self.IDLE:
            self._gen += 1
            gen = self._gen
            self._set_state(self.RECORDING)
            threading.Thread(target=self._record_and_process, args=(gen,), daemon=True).start()
        elif self.state in (self.RECORDING, self.PAUSED):
            self.recorder.stop()

    def cancel_recording(self):
        if self.state in (self.RECORDING, self.PAUSED):
            self._gen += 1
            self._set_state(self.IDLE)
            self.recorder.stop()

    def toggle_pause(self):
        if self.state == self.RECORDING:
            self.recorder.pause()
            self._set_state(self.PAUSED)
        elif self.state == self.PAUSED:
            self._incomplete = False
            self.recorder.resume()
            self._set_state(self.RECORDING)

    def _on_pause_timeout(self):
        self._incomplete = True
        self.recorder.stop()

    def _replay(self):
        if self._last_text:
            self.signals.paste_ready.emit(self._last_text)

    def _improve(self):
        text = QApplication.clipboard().text().strip()
        if not text:
            return
        self._set_state(self.PROCESSING)
        threading.Thread(target=self._run_improve, args=(text,), daemon=True).start()

    def _run_improve(self, text):
        try:
            improved = self.cleaner.improve(text)
            self.signals.improve_ready.emit(improved)
        except Exception as e:
            self.signals.error.emit(str(e))

    def _record_and_process(self, gen):
        try:
            audio = self.recorder.record()
            if gen != self._gen:
                return
            if audio.size == 0:
                self.signals.result.emit("__empty__")
                return
            self.signals.result.emit("__processing__")
            raw   = self.transcriber.transcribe(audio)
            if gen != self._gen:
                return
            clean = self.cleaner.clean(raw)
            if gen != self._gen:
                return
            self.signals.result.emit(clean)
        except Exception as e:
            if gen == self._gen:
                self.signals.error.emit(str(e))

    def _on_result(self, text):
        if text == "__processing__":
            self._set_state(self.PROCESSING)
            return
        if text == "__empty__":
            self._incomplete = False
            self._set_state(self.IDLE)
            return
        if self._incomplete:
            self._incomplete = False
            self._set_state(self.IDLE)
            return
        self._last_text = text
        self._set_state(self.IDLE)
        self.signals.paste_ready.emit(text)

    def _on_error(self, error):
        print(f"[Moon error] {error}")
        self._set_state(self.IDLE)
