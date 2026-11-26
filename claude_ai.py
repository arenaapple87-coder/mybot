import base64
import logging

import anthropic

from config import ANTHROPIC_API_KEY

MODEL = "claude-haiku-4-5"

# Асинхронный клиент: пока ИИ думает над ответом одному человеку,
# бот продолжает отвечать остальным.
client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

ERROR_TEXT = "⚠️ Не получилось получить ответ. Попробуй ещё раз через минуту."

SYSTEM_PROMPT = """You are a smart AI assistant in a Telegram bot.

LANGUAGE RULE: Always respond in the same language the user writes in.
- If the user writes in English — respond in English
- If the user writes in Russian — respond in Russian
- If the user writes in Arabic — respond in Arabic
- If the user writes in Ukrainian — respond in Ukrainian
- And so on for any other language

If the user sends a test or assignment — give the correct specific answer.
If it's a multiple choice question (A, B, C, D) — state the correct answer and explain why.
Solve problems, equations, translate texts — help with any educational tasks.
Be helpful, concise and friendly.

FORMATTING: You may use **bold**, `code` and ``` code blocks ```. Do not use tables."""


class AIError(Exception):
    pass


def _clean_history(messages: list) -> list:
    """API требует, чтобы диалог начинался с сообщения пользователя."""
    while messages and messages[0]["role"] != "user":
        messages = messages[1:]
    return messages


async def ask_claude(messages: list, max_tokens: int = 1024) -> str:
    try:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=_clean_history(messages),
        )
        return response.content[0].text
    except Exception as e:
        logging.exception("Claude API error")
        raise AIError(str(e)) from e


async def ask_claude_with_image(image_data: bytes, mime_type: str, caption: str = "") -> str:
    image_b64 = base64.standard_b64encode(image_data).decode("utf-8")
    content = [
        {
            "type": "image",
            "source": {"type": "base64", "media_type": mime_type, "data": image_b64},
        },
        {
            "type": "text",
            "text": caption or "Реши это задание. Если это тест с вариантами — укажи правильный ответ.",
        },
    ]
    return await ask_claude([{"role": "user", "content": content}])
