from groq import Groq
from config import GROQ_API_KEY

TITLE_PROMPT = """Generá un título corto y descriptivo (máximo 6 palabras) para el siguiente texto.
Solo devolvé el título, sin comillas, sin puntuación al final, sin explicaciones."""

IMPROVE_PROMPT = """Eres un editor de texto profesional. Tu tarea es mejorar el texto que te den.

Reglas:
- Conserva todas las ideas del original
- Mejora la redacción, claridad y fluidez
- Corrige gramática y puntuación
- Elimina muletillas y repeticiones
- NUNCA cambies el significado
- Devuelve solo el texto mejorado, sin explicaciones ni comillas"""

TRANSLATE_PROMPT = """Eres un transcriptor y editor. Tu tarea es limpiar texto transcrito de audio del sistema.

Reglas de idioma:
- Si el texto está en español → devuélvelo en español
- Si el texto está en inglés → devuélvelo en inglés
- Si el texto está en cualquier otro idioma → tradúcelo al inglés

Reglas de edición:
- Elimina muletillas, repeticiones y ruido de transcripción
- Corrige gramática y puntuación
- Conserva todas las ideas sin resumir ni omitir
- Devuelve solo el texto limpio, sin explicaciones"""

SYSTEM_PROMPT = """Eres un editor de texto. Tu única tarea es limpiar texto dictado por voz.

Reglas estrictas:
- Conserva TODAS las ideas y palabras del original, sin excepción
- Solo elimina muletillas ("eh", "mmm", "o sea", "tipo", "bueno")
- Solo elimina repeticiones exactas de palabras
- Agrega puntuación correcta
- Corrige gramática mínima si es necesario
- NUNCA resumas, recortes, ni omitas contenido
- NUNCA cambies el significado ni combines frases
- Devuelve solo el texto corregido, sin explicaciones

Corrección de nombres propios y terminología (Whisper los transcribe mal):
- "Sigma", "sigma", "figma" → Figma
- "Log seek", "logsec", "log sec", "logsick" → Logseq
- "Absidian", "absidian", "obsidien" → Obsidian
- "Notion", "noción" (como app) → Notion
- "design system", "Design System" → Design System
- "moodboard", "mood board", "Moodboard" → Moodboard
- "wireframe", "wire frame" → Wireframe
- "prototype", "prototipo" → Prototipo (mantener en español si el resto es en español)
- "user flow", "flujo de usuario" → User Flow
- "user persona", "persona" (en contexto UX) → User Persona
- "information architecture" → Information Architecture
- "onboarding" → Onboarding
- "handoff", "hand off" → Handoff
- "design token", "design tokens" → Design Token / Design Tokens
- "component library" → Component Library
- "style guide", "style guides" → Style Guide / Style Guides
- "stakeholder", "stake holder", "Stakeholder" → Stakeholder (siempre con mayúscula)
- "Mundo", "mundo", "Munn", "Mon" cuando se refiere al proyecto o app → Moon
- "librería de marca", "brand library" → Brand Library"""


class Cleaner:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    def clean(self, raw_text: str) -> str:
        if not raw_text.strip():
            return ""
        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Texto dictado a limpiar:\n{raw_text}"},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()

    def improve(self, text: str) -> str:
        if not text.strip():
            return text
        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": IMPROVE_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()

    def query(self, question: str, context: str) -> str:
        system = "Eres un asistente que responde preguntas basándose en el contenido de una nota. Responde en el mismo idioma de la pregunta. Sé conciso pero completo. Si la respuesta no está en el contenido, dilo claramente."
        user = f"Contenido de la nota:\n{context}\n\nPregunta: {question}" if context else question
        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    def generate_title(self, text: str) -> str:
        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": TITLE_PROMPT},
                {"role": "user", "content": text[:500]},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    def translate(self, text: str) -> str:
        if not text.strip():
            return text
        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": TRANSLATE_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
