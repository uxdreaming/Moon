from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QCursor, QBrush

HANDLE_SIZE = 10
MIN_SIZE = 20


class RegionSelector(QWidget):
    region_selected = pyqtSignal(QRect)
    cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        self._rect = QRect()
        self._drawing = False
        self._start = QPoint()

        self._drag_handle = None
        self._drag_start = QPoint()
        self._rect_at_drag = QRect()

    def _handles(self):
        if self._rect.isNull():
            return {}
        r = self._rect.normalized()
        cx = r.center().x()
        cy = r.center().y()
        hs = HANDLE_SIZE // 2
        return {
            'tl': QRect(r.left() - hs, r.top() - hs, HANDLE_SIZE, HANDLE_SIZE),
            'tc': QRect(cx - hs, r.top() - hs, HANDLE_SIZE, HANDLE_SIZE),
            'tr': QRect(r.right() - hs, r.top() - hs, HANDLE_SIZE, HANDLE_SIZE),
            'ml': QRect(r.left() - hs, cy - hs, HANDLE_SIZE, HANDLE_SIZE),
            'mr': QRect(r.right() - hs, cy - hs, HANDLE_SIZE, HANDLE_SIZE),
            'bl': QRect(r.left() - hs, r.bottom() - hs, HANDLE_SIZE, HANDLE_SIZE),
            'bc': QRect(cx - hs, r.bottom() - hs, HANDLE_SIZE, HANDLE_SIZE),
            'br': QRect(r.right() - hs, r.bottom() - hs, HANDLE_SIZE, HANDLE_SIZE),
        }

    def _cursor_for_handle(self, handle):
        cursors = {
            'tl': Qt.CursorShape.SizeFDiagCursor,
            'br': Qt.CursorShape.SizeFDiagCursor,
            'tr': Qt.CursorShape.SizeBDiagCursor,
            'bl': Qt.CursorShape.SizeBDiagCursor,
            'tc': Qt.CursorShape.SizeVerCursor,
            'bc': Qt.CursorShape.SizeVerCursor,
            'ml': Qt.CursorShape.SizeHorCursor,
            'mr': Qt.CursorShape.SizeHorCursor,
        }
        return QCursor(cursors.get(handle, Qt.CursorShape.SizeAllCursor))

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        pos = event.position().toPoint()

        if not self._rect.isNull():
            for name, hrect in self._handles().items():
                if hrect.contains(pos):
                    self._drag_handle = name
                    self._drag_start = pos
                    self._rect_at_drag = self._rect.normalized()
                    return
            if self._rect.normalized().contains(pos):
                self._drag_handle = 'move'
                self._drag_start = pos
                self._rect_at_drag = self._rect.normalized()
                self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
                return

        self._drawing = True
        self._start = pos
        self._rect = QRect(pos, pos)
        self._drag_handle = None
        self.update()

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()

        if self._drawing:
            self._rect = QRect(self._start, pos)
            self.update()
            return

        if self._drag_handle:
            delta = pos - self._drag_start
            r = QRect(self._rect_at_drag)

            if self._drag_handle == 'move':
                r.translate(delta)
            elif self._drag_handle == 'tl':
                r.setTopLeft(r.topLeft() + delta)
            elif self._drag_handle == 'tc':
                r.setTop(r.top() + delta.y())
            elif self._drag_handle == 'tr':
                r.setTopRight(r.topRight() + delta)
            elif self._drag_handle == 'ml':
                r.setLeft(r.left() + delta.x())
            elif self._drag_handle == 'mr':
                r.setRight(r.right() + delta.x())
            elif self._drag_handle == 'bl':
                r.setBottomLeft(r.bottomLeft() + delta)
            elif self._drag_handle == 'bc':
                r.setBottom(r.bottom() + delta.y())
            elif self._drag_handle == 'br':
                r.setBottomRight(r.bottomRight() + delta)

            if r.width() >= MIN_SIZE and r.height() >= MIN_SIZE:
                self._rect = r
            self.update()
            return

        if not self._rect.isNull():
            for name, hrect in self._handles().items():
                if hrect.contains(pos):
                    self.setCursor(self._cursor_for_handle(name))
                    return
            if self._rect.normalized().contains(pos):
                self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
                return
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drawing = False
            self._drag_handle = None
            self.update()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            rect = self._rect.normalized()
            if rect.width() > MIN_SIZE and rect.height() > MIN_SIZE:
                self.hide()
                self.region_selected.emit(rect)
        elif event.key() == Qt.Key.Key_Escape:
            self.hide()
            self.cancelled.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))

        if not self._rect.isNull():
            r = self._rect.normalized()

            painter.fillRect(r, QColor(0, 0, 0, 0))
            painter.setPen(QPen(QColor("#5de0e0"), 2))
            painter.drawRect(r)

            painter.setPen(QPen(QColor("#f5f5f7"), 1))
            painter.drawText(r.left() + 4, r.top() - 6,
                             f"{r.width()} × {r.height()}")

            painter.setPen(QPen(QColor("#5de0e0"), 1))
            painter.setBrush(QBrush(QColor("#1c1c1e")))
            for hrect in self._handles().values():
                painter.drawRect(hrect)

        painter.setPen(QPen(QColor("#5de0e0"), 1))
        painter.drawText(
            self.rect().center().x() - 120,
            self.rect().bottom() - 30,
            "Arrastrá para seleccionar  •  Enter para confirmar  •  Esc para cancelar"
        )
