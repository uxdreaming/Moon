import os
import re



def _read_key(name):
    value = os.getenv(name, "")
    if value:
        return value
    try:
        with open(os.path.expanduser("~/.bashrc")) as f:
            for line in f:
                m = re.match(rf'^export {name}="([^"]+)"', line.strip())
                if m:
                    return m.group(1)
    except Exception:
        pass
    return ""


GROQ_API_KEY   = _read_key("GROQ_API_KEY")
GEMINI_API_KEY = _read_key("GEMINI_API_KEY")
SAMPLE_RATE    = 16000
CHUNK_SECONDS  = 30
GLOSSARY_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "glossary.txt")
