# 🌕 Moon

**A silent observer that lives on your desktop.**  
Moon floats over your workspace and captures what matters — your voice, your screen, your audio — without ever asking you to stop what you're doing.

---

## Two modes. One bubble.

### 🎤 Dictate &nbsp;`Alt + F5`
Talk. Moon transcribes your voice and pastes the cleaned result directly into whatever you're working on. No switching windows, no clicking record.

- Double-tap `Right Ctrl` — start / stop
- `AltGr` — pause / resume
- Stops automatically after 10 seconds of silence

### ⚡ Full Sense &nbsp;`Alt + F6`
Draw a region around any video, meeting or tutorial. Moon listens to the system audio and watches the screen at the same time. When you stop, it saves a complete note to Obsidian — transcription and visual analysis combined.

- Draw a capture region over what you want Moon to watch
- Runs silently in the background while you work elsewhere
- Stops automatically after 20 minutes of silence
- One Obsidian note per session, automatically titled and tagged

---

## Hotkeys

| Hotkey | Action |
|--------|--------|
| `F4` | Launch / kill Moon |
| `Alt + F5` | Dictate mode |
| `Alt + F6` | Full Sense mode |
| Double-tap `Right Ctrl` | Start / stop recording (Dictate) |
| `AltGr` | Pause / resume (Dictate) |

---

## Stack

| | |
|--|--|
| **PyQt6** | Floating bubble UI |
| **Groq Whisper** `whisper-large-v3` | Audio transcription |
| **Groq Llama** `llama-3.1-8b-instant` | Text cleanup and translation |
| **Google Gemini** | Visual frame analysis *(optional)* |
| **sounddevice** | Microphone input |
| **soundfile** | Audio encoding |
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
export GEMINI_API_KEY="your_key"   # optional — enables visual analysis
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
