"""Распознавание голосовых. Работает через OpenAI или Groq — какой ключ задан."""
import logging

import httpx

from config import OPENAI_API_KEY, GROQ_API_KEY

if OPENAI_API_KEY:
    URL, KEY, MODEL = "https://api.openai.com/v1/audio/transcriptions", OPENAI_API_KEY, "gpt-4o-mini-transcribe"
elif GROQ_API_KEY:
    URL, KEY, MODEL = "https://api.groq.com/openai/v1/audio/transcriptions", GROQ_API_KEY, "whisper-large-v3-turbo"
else:
    URL = KEY = MODEL = None


def voice_enabled() -> bool:
    return bool(KEY)


async def transcribe(audio: bytes, filename: str = "voice.ogg") -> str:
    """Возвращает распознанный текст или пустую строку при ошибке."""
    try:
        async with httpx.AsyncClient(timeout=60) as http:
            response = await http.post(
                URL,
                headers={"Authorization": f"Bearer {KEY}"},
                data={"model": MODEL, "response_format": "json"},
                files={"file": (filename, audio, "audio/ogg")},
            )
            response.raise_for_status()
            return (response.json().get("text") or "").strip()
    except Exception:
        logging.exception("Voice transcription error")
        return ""
