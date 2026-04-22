import threading
from core.audio import AudioRecorder
from core.vision import VisionAnalyzer
from ui.region_selector import RegionSelector
from ui.robot_controls import RobotControls
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QMenu
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer, pyqtSignal, QObject, QRectF, QSize
from PyQt6.QtGui import QFont, QCursor, QPainter, QColor, QPen, QBrush, QPainterPath


BUBBLE_SIZE = 80
RADIUS = 26

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
    QMenu::item:selected {
        background: #2c2c2e;
    }
    QMenu::separator {
        height: 1px;
        background: #3a3a3c;
        margin: 3px 8px;
    }
    QMenu::indicator {
        width: 0px;
    }
    QMenu::item:checked {
        color: #f5f5f7;
        background: #3a3a3c;
    }
"""


class WorkerSignals(QObject):
    result = pyqtSignal(str)
    error = pyqtSignal(str)
    paste_ready = pyqtSignal(str)
    improve_ready = pyqtSignal(str)
    capture_focus = pyqtSignal()


class Bubble(QWidget):
    IDLE       = "idle"
    RECORDING  = "recording"
    LISTENING  = "listening"
    SELECTING  = "selecting"
    QUERYING   = "querying"
    PAUSED     = "paused"
    PROCESSING = "processing"
    RESULT     = "result"

    def __init__(self, recorder, transcriber, cleaner):
        super().__init__()
        self.recorder = recorder
        self.transcriber = transcriber
        self.cleaner = cleaner
        self.signals = WorkerSignals()
        self.signals.result.connect(self._on_result)
        self.signals.error.connect(self._on_error)
        self._drag_pos = QPoint()
        self._dot_count = 0
        self._last_text = ""
        self._border = QColor("#3a3a3c")
        self._mode = "mic"
        self._last_obsidian_note = ""
        self.query_recorder = AudioRecorder()
        self._capture_region = None
        self._screenshots = []
        self.vision = VisionAnalyzer()
        self._region_selector = None
        self._robot_controls = None

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
        self._icon.setSizePolicy(
            self._icon.sizePolicy().horizontalPolicy(),
            self._icon.sizePolicy().verticalPolicy()
        )

        layout.addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self._dot_timer = QTimer()
        self._dot_timer.timeout.connect(self._tick_dots)

        self._pulse_timer = QTimer()
        self._pulse_timer.timeout.connect(self._tick_pulse)
        self._pulse_value = 0.0
        self._pulse_dir = 1

        self._pause_timeout = QTimer()
        self._pause_timeout.setSingleShot(True)
        self._pause_timeout.timeout.connect(self._on_pause_timeout)
        self._incomplete = False

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

        PURPLE = "#a78bfa"
        CYAN   = "#5de0e0"

        if state == self.IDLE:
            self._set_mode_label("", "transparent")
            self._border = QColor("#3a3a3c")
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        elif state == self.RECORDING:
            self._set_mode_label("Dict", PURPLE)
            self._border = QColor(PURPLE)
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        elif state == self.SELECTING:
            self._set_mode_label("Capt", CYAN)
            self._border = QColor(CYAN)
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        elif state == self.LISTENING:
            self._set_mode_label("Capt", CYAN)
            self._border = QColor(CYAN)
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self._pulse_timer.start(40)

        elif state == self.QUERYING:
            self._set_mode_label("Dict", PURPLE)
            self._border = QColor(PURPLE)
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        elif state == self.PAUSED:
            self._set_mode_label("Dict", PURPLE)
            self._border = QColor("#b8d4fb")
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self._pulse_timer.start(60)
            self._pause_timeout.start(5 * 60 * 1000)

        elif state == self.PROCESSING:
            label = "Capt" if self._mode == "system" else "Dict"
            color = CYAN if self._mode == "system" else PURPLE
            self._set_mode_label(label, color)
            self._border = QColor("#ede0a8")
            self._dot_timer.start(350)

        elif state == self.RESULT:
            label = "Capt" if self._mode == "system" else "Dict"
            color = CYAN if self._mode == "system" else PURPLE
            self._set_mode_label(label, color)
            self._border = QColor("#b4dcc4")
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.update()

    def _set_mode_label(self, text, color):
        if text:
            self._icon.setFont(QFont("Sans", 13, QFont.Weight.Bold))
            self._icon.setText(text)
            self._icon.setStyleSheet(f"background: transparent; border: none; color: {color};")
        else:
            self._icon.setFont(QFont("Noto Color Emoji", 24))
            self._icon.setText("🌕")
            self._icon.setStyleSheet("background: transparent; border: none;")

    def _tick_dots(self):
        self._dot_count = (self._dot_count + 1) % 4
        dots = "·" * self._dot_count
        current = self._icon.text().rstrip("·")
        self._icon.setText(f"{current}{dots}")

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
            shadow_color = QColor(0, 0, 0, 18 - i)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(shadow_color))
            sp = QPainterPath()
            sp.addRoundedRect(shadow_rect, RADIUS, RADIUS)
            painter.drawPath(sp)

        painter.setBrush(QBrush(self._bg))
        if self.state == self.LISTENING:
            alpha = int(160 + 95 * self._pulse_value)
            border_color = QColor(93, 224, 224, alpha)
            width = 4.0 + 2.0 * self._pulse_value
            painter.setPen(QPen(border_color, width))
        elif self.state == self.PAUSED:
            alpha = int(130 + 125 * self._pulse_value)
            border_color = QColor(184, 212, 251, alpha)
            painter.setPen(QPen(border_color, 4.0))
        else:
            painter.setPen(QPen(self._border, 4.0))
        path = QPainterPath()
        path.addRoundedRect(rect, RADIUS, RADIUS)
        painter.drawPath(path)

    def contextMenuEvent(self, event):
        self.signals.capture_focus.emit()
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)

        if self.state == self.LISTENING:
            menu.addAction("⏹  Detener escucha", self._stop_listening)
        else:
            mic_action = menu.addAction("🎤  Dictar")
            mic_action.setCheckable(True)
            mic_action.setChecked(self._mode == "mic")
            mic_action.triggered.connect(lambda: self._set_mode("mic"))

            sys_action = menu.addAction("🤖  Escuchar sistema")
            sys_action.setCheckable(True)
            sys_action.setChecked(self._mode == "system")
            sys_action.triggered.connect(self._start_listening)
            menu.addSeparator()
            if self._last_text:
                menu.addAction("↩  Repetir último", self._replay)
            menu.addAction("✨  Mejorar texto", self._improve)
        geo = self.frameGeometry()
        screen = QApplication.primaryScreen().geometry()
        menu_width = 200
        if geo.right() + menu_width < screen.right():
            x = geo.right()
        else:
            x = geo.left() - menu_width
        y = geo.top()
        menu.exec(QPoint(x, y))

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

    def _set_mode(self, mode):
        self._mode = mode

    def _start_listening(self):
        self._mode = "system"
        self._screenshots = []
        self._set_state(self.LISTENING)
        self._robot_controls = RobotControls(self)
        self._robot_controls.pause_clicked.connect(self._on_robot_pause)
        self._robot_controls.stop_clicked.connect(self._stop_listening)
        self._robot_controls.show()
        threading.Thread(target=self._listen_and_process, daemon=True).start()
        if self._capture_region:
            threading.Thread(target=self._capture_loop, daemon=True).start()

    def _stop_listening(self):
        if self._robot_controls:
            self._robot_controls.hide()
            self._robot_controls = None
        self.recorder.stop()

    def _on_robot_pause(self):
        if self.state == self.LISTENING:
            self.recorder.pause()
        else:
            self.recorder.resume()

    def _capture_loop(self):
        import mss
        import io
        import time
        with mss.mss() as sct:
            while self.state == self.LISTENING:
                try:
                    shot = sct.grab(self._capture_region)
                    img_bytes = mss.tools.to_png(shot.rgb, shot.size)
                    self._screenshots.append(img_bytes)
                except Exception as e:
                    print(f"[Moon capture] {e}")
                time.sleep(10)

    def _on_region_selected(self, rect: QRect):
        self._capture_region = {
            'left': rect.left(),
            'top': rect.top(),
            'width': rect.width(),
            'height': rect.height(),
        }
        self._start_listening()

    def f5_mic_mode(self):
        if self.state == self.LISTENING:
            self._stop_listening()
        if self.state == self.IDLE:
            self._mode = "mic"
            self._border = QColor("#e8b4b4")
            self.update()
            QTimer.singleShot(600, lambda: self._set_state(self.IDLE))

    def f6_system_mode(self):
        if self.state in (self.RECORDING, self.PAUSED):
            return
        if self.state == self.IDLE:
            self._set_state(self.SELECTING)
            self._region_selector = RegionSelector()
            self._region_selector.region_selected.connect(self._on_region_selected)
            self._region_selector.cancelled.connect(lambda: self._set_state(self.IDLE))
            self._region_selector.show()
            self._region_selector.activateWindow()
            self._region_selector.setFocus()
        elif self.state in (self.LISTENING, self.SELECTING):
            if self._region_selector:
                self._region_selector.hide()
            self._stop_listening()

    def toggle_recording(self):
        if self.state == self.IDLE:
            self._set_state(self.RECORDING)
            threading.Thread(target=self._record_and_process, daemon=True).start()
        elif self.state in (self.RECORDING, self.PAUSED):
            self.recorder.stop()
        elif self.state == self.LISTENING:
            threading.Thread(target=self._record_and_query, daemon=True).start()
        elif self.state == self.QUERYING:
            self.query_recorder.stop()

    def _on_pause_timeout(self):
        self._incomplete = True
        self.recorder.stop()

    def toggle_pause(self):
        if self.state == self.RECORDING:
            self.recorder.pause()
            self._set_state(self.PAUSED)
        elif self.state == self.PAUSED:
            self._incomplete = False
            self.recorder.resume()
            self._set_state(self.RECORDING)

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

    def _record_and_process(self):
        try:
            audio = self.recorder.record()
            if audio.size == 0:
                self.signals.result.emit("__empty__")
                return
            self.signals.result.emit("__processing__")
            raw = self.transcriber.transcribe(audio)
            clean = self.cleaner.clean(raw)
            self.signals.result.emit(clean)
        except Exception as e:
            self.signals.error.emit(str(e))

    def _record_and_query(self):
        import os
        from datetime import datetime
        self._set_state(self.QUERYING)
        try:
            audio = self.query_recorder.record()
            if audio.size == 0:
                self._set_state(self.LISTENING)
                return
            raw = self.transcriber.transcribe(audio)
            question = self.cleaner.clean(raw)
            if not question.strip():
                self._set_state(self.LISTENING)
                return

            context = ""
            if self._last_obsidian_note:
                note_path = os.path.join(
                    os.path.expanduser("~"), "Documentos", "Oblivion", "Moon",
                    self._last_obsidian_note + ".md"
                )
                if os.path.exists(note_path):
                    with open(note_path, "r", encoding="utf-8") as f:
                        context = f.read()

            answer = self.cleaner.query(question, context)
            title = self.cleaner.generate_title(question)
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            safe_title = "".join(c for c in title if c not in r'\/:*?"<>|')
            filename = f"{now} - {safe_title}.md"
            path = os.path.join(os.path.expanduser("~"), "Documentos", "Oblivion", "Moon", filename)
            source_link = f"[[{self._last_obsidian_note}]]" if self._last_obsidian_note else ""
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n#Moon\n")
                if source_link:
                    f.write(f"\n**Fuente:** {source_link}\n")
                f.write(f"\n**Pregunta:** {question}\n\n**Respuesta:**\n{answer}\n")
            self._set_state(self.LISTENING)
        except Exception as e:
            print(f"[Moon query] {e}")
            self._set_state(self.LISTENING)

    def _listen_and_process(self):
        import os
        from datetime import datetime
        try:
            audio = self.recorder.record_system()
            if audio.size == 0:
                self.signals.result.emit("__empty__")
                return
            self.signals.result.emit("__processing__")
            raw = self.transcriber.transcribe(audio)
            clean = self.cleaner.translate(raw)

            visual_analysis = ""
            if self._screenshots:
                visual_analysis = self.vision.analyze(self._screenshots, clean)

            title = self.cleaner.generate_title(clean)
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            safe_title = "".join(c for c in title if c not in r'\/:*?"<>|')
            filename = f"{now} - {safe_title}.md"
            path = os.path.join(os.path.expanduser("~"), "Documentos", "Oblivion", "Moon", filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n#Moon\n\n")
                f.write(f"## Transcripción\n{clean}\n")
                if visual_analysis:
                    f.write(f"\n## Análisis visual\n{visual_analysis}\n")
            self._last_obsidian_note = filename[:-3]
            self._screenshots = []
            self.signals.result.emit("__obsidian__")
        except Exception as e:
            self.signals.error.emit(str(e))

    def _on_result(self, text):
        if text == "__processing__":
            self._set_state(self.PROCESSING)
            return
        if text == "__empty__":
            self._incomplete = False
            self._set_state(self.IDLE)
            return
        if text == "__obsidian__":
            self._set_state(self.RESULT)
            QTimer.singleShot(700, lambda: self._set_state(self.IDLE))
            return
        if self._incomplete:
            self._incomplete = False
            self._save_incomplete(text)
            self._set_state(self.RESULT)
            QTimer.singleShot(700, lambda: self._set_state(self.IDLE))
            return
        self._last_text = text
        self._set_state(self.RESULT)
        self.signals.paste_ready.emit(text)
        QTimer.singleShot(700, lambda: self._set_state(self.IDLE))

    def _save_incomplete(self, text):
        import os
        from datetime import datetime
        try:
            title = self.cleaner.generate_title(text)
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            safe_title = "".join(c for c in title if c not in r'\/:*?"<>|')
            filename = f"{now} - ⚠️ {safe_title}.md"
            path = os.path.join(os.path.expanduser("~"), "Documentos", "Oblivion", "Moon", filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# ⚠️ Audio incompleto — {title}\n#Moon\n\n{text}\n")
        except Exception as e:
            print(f"[Moon incomplete save] {e}")

    def _on_error(self, error):
        print(f"[Moon error] {error}")
        self._set_state(self.IDLE)
