# 🌕 Moon

**A floating bubble that lives on your desktop and types what you say.**  
Talk. Moon transcribes your voice and pastes the result directly into whatever you're working on.

---

## How it works

Double-tap `Right Ctrl` to start recording. A 🎙️ appears with a pulsing purple border. Talk. Double-tap again to stop — Moon transcribes and pastes into the focused window automatically.

While recording you can pause with `AltGr` and resume with `AltGr` again. Recording also stops automatically after 10 seconds of silence.

If your microphone isn't connected, the bubble shows 🎤 with a red border and ignores recording attempts until it's plugged back in.

---

## Hotkeys

| Hotkey | Action |
|--------|--------|
| Double-tap `Right Ctrl` | Start / stop recording |
| `AltGr` | Pause / resume |
| Double-tap `Menu` | Cancel recording (discards audio) |

Toggle Moon on/off with a shell script bound to any key in your window manager.

---

## Stack

| | |
|--|--|
| **PyQt6** | Floating bubble UI |
| **Groq Whisper** `whisper-large-v3` | Audio transcription |
| **Groq Llama** `llama-3.1-8b-instant` | Text cleanup |
| **sounddevice** | Microphone input |
| **pynput** | Global hotkeys |
| **Xlib** | X11 window focus detection |

---

## Install

```bash
git clone https://github.com/uxdreaming/Moon
cd Moon
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Add to `~/.bashrc`:

```bash
export GROQ_API_KEY="your_key"
```

---

## Qtile

Bind a key to toggle Moon on and off:

```python
Key([], "F4", lazy.spawn("/path/to/Moon/toggle.sh")),
```

---

## License

MIT © 2026 uxdreaming
