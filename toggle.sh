#!/bin/bash
if pgrep -f "Moon/main.py" > /dev/null; then
    pkill -f "Moon/main.py"
else
    source ~/.profile 2>/dev/null || true
    [ -f ~/.bashrc ] && grep -E "^export (GROQ|GEMINI)_API_KEY" ~/.bashrc | while read line; do eval "$line"; done
    export PYTHONUNBUFFERED=1
    /home/aru/ZX/Projects/Moon/.venv/bin/python /home/aru/ZX/Projects/Moon/main.py >> /tmp/moon.log 2>&1 &
fi
