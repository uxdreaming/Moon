from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import QSize, Qt


def _make_icon():
    px = QPixmap(QSize(32, 32))
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#44cc88"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(4, 4, 24, 24)
    p.end()
    return QIcon(px)


def create_tray(app, bubble):
    tray = QSystemTrayIcon(_make_icon(), app)
    menu = QMenu()
    menu.addAction("Mostrar / Ocultar", lambda: _toggle(bubble))
    menu.addSeparator()
    menu.addAction("Salir", app.quit)
    tray.setContextMenu(menu)
    tray.setToolTip("Moon")
    tray.activated.connect(lambda reason: _toggle(bubble) if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
    tray.show()
    return tray


def _toggle(bubble):
    if bubble.isVisible():
        bubble.hide()
    else:
        bubble.show()
        bubble.raise_()
        bubble.activateWindow()
