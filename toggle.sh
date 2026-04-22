#!/bin/bash
if pgrep -f "Moon/main.py" > /dev/null; then
    pkill -f "Moon/main.py"
else
    source ~/.bashrc
    export PYTHONUNBUFFERED=1
    /home/aru/ZX/Projects/Moon/.venv/bin/python /home/aru/ZX/Projects/Moon/main.py >> /tmp/moon.log 2>&1 &
fi
