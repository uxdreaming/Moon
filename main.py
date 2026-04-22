import sys
import time
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from pynput import keyboard
from pynput.keyboard import Controller as KbController, Key
from Xlib import display as xdisplay, X
from Xlib.protocol import event as xevent
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



def set_sticky(window_id):
    try:
        d = xdisplay.Display()
        root = d.screen().root
        win = d.create_resource_object('window', window_id)
        _NET_WM_STATE = d.intern_atom('_NET_WM_STATE')
        _NET_WM_STATE_STICKY = d.intern_atom('_NET_WM_STATE_STICKY')
        ev = xevent.ClientMessage(
            window=win,
            client_type=_NET_WM_STATE,
            data=(32, [1, _NET_WM_STATE_STICKY, 0, 0, 0])
        )
        mask = X.SubstructureRedirectMask | X.SubstructureNotifyMask
        root.send_event(ev, event_mask=mask)
        d.flush()
    except Exception as e:
        print(f"[Moon sticky] {e}")


def focus_window(window_id):
    try:
        d = xdisplay.Display()
        w = d.create_resource_object('window', window_id)
        w.set_input_focus(X.RevertToParent, X.CurrentTime)
        d.sync()
    except Exception as e:
        print(f"[Moon focus] {e}")


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

    recorder = AudioRecorder()
    transcriber = Transcriber()
    cleaner = Cleaner()

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
        window_id = state['focused_window']
        paste_to_window(window_id, text)

    def on_capture_focus():
        state['focused_window'] = get_focused_window_id()

    bubble.signals.capture_focus.connect(on_capture_focus)
    bubble.signals.paste_ready.connect(on_paste_ready)

    def on_improve_ready(text):
        window_id = state['focused_window']
        paste_to_window(window_id, text)

    bubble.signals.improve_ready.connect(on_improve_ready)

    _last_rctrl = [0.0]
    DOUBLE_TAP_MS = 400
    _alt_held = [False]

    def on_press(key):
        is_altgr = key in (keyboard.Key.alt_r, keyboard.Key.alt_gr) or getattr(key, 'vk', None) == 65027

        if is_altgr:
            QTimer.singleShot(0, bubble.toggle_pause)

        elif key == keyboard.Key.alt_l or key == keyboard.Key.alt:
            _alt_held[0] = True

        elif key == keyboard.Key.ctrl_r:
            now = time.time() * 1000
            if now - _last_rctrl[0] < DOUBLE_TAP_MS:
                _last_rctrl[0] = 0.0
                state['focused_window'] = get_focused_window_id()
                QTimer.singleShot(0, bubble.toggle_recording)
            else:
                _last_rctrl[0] = now

        elif key == keyboard.Key.f5 and _alt_held[0]:
            QTimer.singleShot(0, bubble.f5_mic_mode)

        elif key == keyboard.Key.f6 and _alt_held[0]:
            QTimer.singleShot(0, bubble.f6_system_mode)

    def on_release(key):
        if key in (keyboard.Key.alt_l, keyboard.Key.alt, keyboard.Key.alt_r, keyboard.Key.alt_gr) \
                or getattr(key, 'vk', None) == 65027:
            _alt_held[0] = False

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.daemon = True
    listener.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
