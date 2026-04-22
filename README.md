# 🌕 Moon

> A floating intelligence layer for Linux — always listening, always watching, never in the way.

Moon is a minimal floating bubble that lives on your Linux desktop. Two modes, two hotkeys, zero friction.

---

## Modes

### 🎤 Dictate — `F5`
Speak. Moon transcribes and pastes clean text directly into your active window.

- Double `Ctrl Right` → start / stop recording
- `AltGr` → pause / resume
- Powered by Groq Whisper + LLM cleanup

### ⚡ Full Sense — `F6`
Point Moon at anything on your screen — a video, a meeting, a tutorial. It listens and watches simultaneously, then saves a structured note to Obsidian when you stop.

- Draw a capture region with the grabber
- Moon records system audio and takes screenshots in parallel
- Output: transcription + visual analysis merged into a single Obsidian note

---

## Controls

| Key | Action |
|-----|--------|
| `F4` | Quit Moon |
| `F5` | Dictate mode |
| `F6` | Full Sense mode |
| `F7` / `F8` | Reserved for future modes |
| `Double Ctrl Right` | Start / stop recording (Dictate) |
| `AltGr` | Pause / resume (Dictate) |

---

## Stack

- **PyQt6** — floating bubble UI
- **Groq** — Whisper transcription + Llama text cleanup
- **Google Gemini** — visual analysis (optional)
- **sounddevice** — microphone input
- **parec** — PipeWire/PulseAudio system audio capture
- **pynput** — global hotkeys
- **mss** — screen region capture
- **Xlib** — X11 window management

---

## Setup

```bash
git clone https://github.com/uxdreaming/Moon
cd Moon
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Add your API keys to `~/.bashrc`:

```bash
export GROQ_API_KEY="your_key_here"
export GEMINI_API_KEY="your_key_here"  # optional — enables visual analysis
```

Then run:

```bash
./run.sh
```

Or bind `F4` in your window manager to toggle Moon on and off.

---

## Qtile

In your `config.py`:

```python
Key([], "F4", lazy.spawn("/path/to/Moon/toggle.sh")),
Key([], "F5", lazy.spawn("/path/to/Moon/toggle.sh")),
Key([], "F6", lazy.spawn("/path/to/Moon/toggle.sh")),
```

---

## How notes work

Full Sense captures are saved as **read-only archives** in Obsidian. If you want to build on a note, create a new one and link back to the original — the source is never touched.

---

## License

MIT © 2026 uxdreaming
