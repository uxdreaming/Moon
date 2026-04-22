import io
import numpy as np
import soundfile as sf
from groq import Groq
from config import GROQ_API_KEY, SAMPLE_RATE


class Transcriber:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    def transcribe(self, audio_array: np.ndarray) -> str:
        buf = io.BytesIO()
        sf.write(buf, audio_array, SAMPLE_RATE, format='flac')
        buf.seek(0)
        buf.name = 'audio.flac'

        response = self.client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=buf,
            language="es",
            response_format="text",
        )
        return response.strip() if isinstance(response, str) else response.text.strip()
