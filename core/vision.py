from google import genai
from google.genai import types
from config import GEMINI_API_KEY

VISION_PROMPT = """Estás analizando capturas de pantalla de un video o presentación junto con su transcripción de audio.

Tu tarea:
- Describe lo que se muestra visualmente en las capturas (diagramas, código, slides, personas, texto en pantalla)
- Identifica conceptos clave que se ven pero que pueden no estar en el audio
- Conecta lo visual con lo auditivo cuando sea relevante
- Extrae cualquier texto visible importante (títulos, código, URLs, nombres)
- Sé específico y detallado

Responde en el mismo idioma de la transcripción."""

KEYWORD_PROMPT = """Analizá esta captura de pantalla y devolvé SOLO un keyword descriptivo de 3 a 5 palabras en inglés que describa el contenido principal visible.

Reglas estrictas:
- Solo devolvé el keyword, sin explicaciones ni puntuación
- Usá Title Case
- Separá las palabras con guiones medios (-)
- Máximo 5 palabras
- Ejemplos válidos: UI-Kit-Primary-Button, React-Hooks-useState, Typography-Scale-Heading, Color-System-Dark-Mode"""

MODELS = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash-001"]


class VisionAnalyzer:
    def __init__(self):
        if GEMINI_API_KEY:
            self.client = genai.Client(api_key=GEMINI_API_KEY, http_options={"api_version": "v1"})
        else:
            self.client = None
            print("[Moon vision] Sin GEMINI_API_KEY — análisis visual desactivado")

    def analyze(self, screenshots: list[bytes], transcript: str) -> str:
        if not screenshots or not self.client:
            return ""

        if len(screenshots) > 5:
            step = len(screenshots) / 5
            screenshots = [screenshots[int(i * step)] for i in range(5)]

        parts = [
            types.Part(text=f"{VISION_PROMPT}\n\nTranscripción de audio:\n{transcript}\n\nCapturas de pantalla:"),
        ]
        for img_bytes in screenshots:
            parts.append(types.Part(inline_data=types.Blob(mime_type="image/png", data=img_bytes)))

        for model in MODELS:
            try:
                response = self.client.models.generate_content(model=model, contents=parts)
                return response.text.strip()
            except Exception as e:
                print(f"[Moon vision] {model} failed: {e}")
                continue

        return ""
