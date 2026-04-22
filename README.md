# 🌕 Moon

**A silent observer that lives on your desktop.**  
Moon floats over your workspace and captures what matters — your voice, your screen, your audio — without ever asking you to stop what you're doing.

---

## Two modes. One bubble.

### 🎤 Dictate &nbsp;`Alt + F5`
Talk. Moon transcribes your voice and pastes the cleaned result directly into whatever you're working on. No switching windows, no clicking record.

- `Double Ctrl Right` — start / stop
- `AltGr` — pause / resume

### ⚡ Full Sense &nbsp;`Alt + F6`
Draw a region around any video, meeting or tutorial. Moon listens to the system audio and watches the screen at the same time. When you stop, it saves a complete note to Obsidian — transcription and visual analysis together.

- Draw a capture region over what you want Moon to watch
- Runs silently in the background while you work elsewhere
- One Obsidian note per session, automatically titled and tagged

---

## Hotkeys

| Hotkey | Action |
|--------|--------|
| `F4` | Launch / kill Moon |
| `Alt + F5` | Dictate mode |
| `Alt + F6` | Full Sense mode |
| `Double Ctrl Right` | Record / stop (Dictate) |
| `AltGr` | Pause / resume (Dictate) |

---

## Stack

| | |
|--|--|
| **PyQt6** | Floating bubble UI |
| **Groq** | Whisper transcription + Llama text cleanup |
| **Google Gemini** | Visual frame analysis *(optional)* |
| **sounddevice** | Microphone capture |
| **parec** | System audio via PipeWire / PulseAudio |
| **pynput** | Global hotkeys |
| **mss** | Screen region capture |
| **Xlib** | X11 window management |

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
export GEMINI_API_KEY="your_key"   # optional
```

Run:

```bash
./run.sh
```

---

## Qtile

Bind `F4` to toggle Moon on and off:

```python
Key([], "F4", lazy.spawn("/path/to/Moon/toggle.sh")),
```

---

## How notes work

Full Sense sessions are saved as **read-only archives** in Obsidian.  
If you want to build on a note, create a new one and link it back — the original is never modified.

---

## License

MIT © 2026 uxdreaming
