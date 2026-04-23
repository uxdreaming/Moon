import sys
import time
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from pynput import keyboard
from pynput.keyboard import Controller as KbController, Key
from Xlib import display as xdisplay, X
from core.audio import AudioRecorder
from core.transcriber import Transcriber
from core.cleaner import Cleaner
from ui.bubble import Bubble

TERMINALS = {
    'kitty', 'alacritty', 'st', 'st-256color', 'xterm', 'xterm-256color',
    'urxvt', 'rxvt', 'wezterm', 'foot', 'qterminal', 'konsole', 'tilix',
    'gnome-terminal', 'termite', 'terminator', 'xfce4-terminal',
}

_kb = KbController()


def get_focused_window_id():
    try:
        d = xdisplay.Display()
        return d.get_input_focus().focus.id
    except Exception:
        return None


def get_window_class(window_id):
    try:
        d = xdisplay.Display()
        w = d.create_resource_object('window', window_id)
        wm_class = w.get_wm_class()
        if wm_class:
            return wm_class[1].lower()
    except Exception:
        pass
    return ''


def _send_keys(window_id):
    time.sleep(0.4)
    wm_class = get_window_class(window_id) if window_id else ''
    if wm_class in TERMINALS:
        with _kb.pressed(Key.ctrl):
            with _kb.pressed(Key.shift):
                _kb.tap('v')
    else:
        with _kb.pressed(Key.ctrl):
            _kb.tap('v')


def paste_to_window(window_id, text):
    QApplication.clipboard().setText(" " + text)
    threading.Thread(target=_send_keys, args=(window_id,), daemon=True).start()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    recorder    = AudioRecorder()
    transcriber = Transcriber()
    cleaner     = Cleaner()

    bubble = Bubble(recorder, transcriber, cleaner)

    screen = app.primaryScreen().geometry()
    margin = 16
    bubble.show()

    raise_timer = QTimer()
    raise_timer.timeout.connect(bubble.raise_)
    raise_timer.start(200)

    bubble.move(
        screen.right() - bubble.width() - margin,
        screen.bottom() - bubble.height() - margin,
    )

    state = {'focused_window': None}

    def on_paste_ready(text):
        paste_to_window(state['focused_window'], text)

    def on_capture_focus():
        state['focused_window'] = get_focused_window_id()

    bubble.signals.capture_focus.connect(on_capture_focus)
    bubble.signals.paste_ready.connect(on_paste_ready)

    _last_rctrl      = [0.0]
    _last_menu       = [0.0]
    DOUBLE_TAP_MS    = 400
    _rctrl_held      = [False]
    _menu_held       = [False]
    _rctrl_tap_timer = [None]

    def _fire_pause():
        QTimer.singleShot(0, bubble.toggle_pause)

    def on_press(key):
        is_altgr = key in (keyboard.Key.alt_r, keyboard.Key.alt_gr) or getattr(key, 'vk', None) == 65027

        if is_altgr:
            QTimer.singleShot(0, bubble.learn_word)

        elif key == keyboard.Key.ctrl_r:
            if _rctrl_held[0]:
                return
            _rctrl_held[0] = True
            now = time.time() * 1000
            if now - _last_rctrl[0] < DOUBLE_TAP_MS:
                _last_rctrl[0] = 0.0
                if _rctrl_tap_timer[0]:
                    _rctrl_tap_timer[0].cancel()
                    _rctrl_tap_timer[0] = None
                state['focused_window'] = get_focused_window_id()
                QTimer.singleShot(0, bubble.toggle_recording)
            else:
                _last_rctrl[0] = now
                if _rctrl_tap_timer[0]:
                    _rctrl_tap_timer[0].cancel()
                t = threading.Timer(DOUBLE_TAP_MS / 1000, _fire_pause)
                t.daemon = True
                t.start()
                _rctrl_tap_timer[0] = t

        elif key == keyboard.Key.menu:
            if _menu_held[0]:
                return
            _menu_held[0] = True
            now = time.time() * 1000
            if now - _last_menu[0] < DOUBLE_TAP_MS:
                _last_menu[0] = 0.0
                QTimer.singleShot(0, bubble.cancel_recording)
            else:
                _last_menu[0] = now

    def on_release(key):
        is_altgr = key in (keyboard.Key.alt_r, keyboard.Key.alt_gr) or getattr(key, 'vk', None) == 65027
        if is_altgr:
            pass
        elif key == keyboard.Key.ctrl_r:
            _rctrl_held[0] = False
        elif key == keyboard.Key.menu:
            _menu_held[0] = False

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.daemon = True
    listener.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
