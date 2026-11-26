"""Распознавание голосовых через Groq (модель Whisper). Бесплатный ключ: console.groq.com"""
import logging

import httpx

from config import GROQ_API_KEY

GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
MODEL = "whisper-large-v3-turbo"


def voice_enabled() -> bool:
    return bool(GROQ_API_KEY)


async def transcribe(audio: bytes, filename: str = "voice.ogg") -> str:
    """Возвращает распознанный текст или пустую строку при ошибке."""
    try:
        async with httpx.AsyncClient(timeout=60) as http:
            response = await http.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                data={"model": MODEL, "response_format": "json"},
                files={"file": (filename, audio)},
            )
            response.raise_for_status()
            return (response.json().get("text") or "").strip()
    except Exception:
        logging.exception("Voice transcription error")
        return ""
