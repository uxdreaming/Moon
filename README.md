# 🌕 Moon

> A floating intelligence layer for Linux — always listening, always watching, never in the way.

Moon is a minimal floating bubble for Linux desktops that gives you two powerful capture modes, triggered by keyboard shortcuts, without ever breaking your flow.

---

## Modes

### 🎤 Dictado — `F5`
Speak. Moon transcribes and pastes the cleaned text directly into your active window.

- Double `Ctrl Right` → start / stop recording
- `AltGr` → pause / resume
- Groq Whisper transcription + LLM cleanup

### ⚡ Full Sense — `F6`
Moon watches and listens to whatever is on your screen — a video, a meeting, a tutorial — and saves a structured note to Obsidian automatically.

- Select a capture region with the grabber
- Moon records system audio + screenshots in parallel
- At the end: transcription + visual analysis merged into a single Obsidian note

---

## Controls

| Key | Action |
|-----|--------|
| `F4` | Kill Moon entirely |
| `F5` | Toggle Dictado mode |
| `F6` | Toggle Full Sense mode |
| `F7` / `F8` | Reserved for future modes |
| `Double Ctrl Right` | Record / Stop (Dictado) |
| `AltGr` | Pause / Resume (Dictado) |

---

## Stack

- **PyQt6** — floating bubble UI
- **Groq** — Whisper transcription + Llama cleanup/translation
- **Google Gemini** — visual analysis (optional)
- **sounddevice** — microphone capture
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

Set your API keys in `~/.bashrc`:

```bash
export GROQ_API_KEY="your_key_here"
export GEMINI_API_KEY="your_key_here"  # optional, enables visual analysis
```

Run:

```bash
./run.sh
```

Or bind `F4` in your window manager to toggle Moon on/off.

---

## Qtile Integration

In your `config.py`:

```python
Key([], "F4", lazy.spawn("/path/to/Moon/toggle.sh")),
Key([], "F5", ...),
Key([], "F6", ...),
```

---

## Notes philosophy

Full Sense notes are **read-only archives** in Obsidian. If you derive content from a note, a new linked note is created — the original is never modified.

---

## License

MIT © 2026 uxdreaming
