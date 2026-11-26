import base64
import logging

import anthropic

from config import ANTHROPIC_API_KEY, HISTORY_MAX_CHARS

MODEL = "claude-haiku-4-5"

# Асинхронный клиент: пока ИИ думает над ответом одному человеку,
# бот продолжает отвечать остальным.
client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

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
Be helpful, concise and friendly. Keep answers reasonably short unless the user asks for detail.

FORMATTING: You may use **bold**, `code` and ``` code blocks ```. Do not use tables."""


class AIError(Exception):
    pass


def _prepare_history(messages: list) -> list:
    """Готовит историю для ИИ: начинается с пользователя, старые длинные
    сообщения обрезаются (это сильно экономит деньги на длинных чатах)."""
    while messages and messages[0]["role"] != "user":
        messages = messages[1:]
    prepared = []
    last = len(messages) - 1
    for i, m in enumerate(messages):
        content = m["content"]
        if i != last and isinstance(content, str) and len(content) > HISTORY_MAX_CHARS:
            content = content[:HISTORY_MAX_CHARS] + " […]"
        prepared.append({"role": m["role"], "content": content})
    return prepared


async def ask_claude(messages: list, max_tokens: int = 1024) -> str:
    try:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=_prepare_history(messages),
        )
        return response.content[0].text
    except Exception as e:
        logging.exception("Claude API error")
        raise AIError(str(e)) from e


async def ask_claude_with_image(image_data: bytes, mime_type: str, prompt: str) -> str:
    content = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": mime_type,
                "data": base64.standard_b64encode(image_data).decode("utf-8"),
            },
        },
        {"type": "text", "text": prompt},
    ]
    return await ask_claude([{"role": "user", "content": content}])


async def ask_claude_with_pdf(pdf_data: bytes, prompt: str) -> str:
    """Для PDF-сканов без текста: ИИ смотрит на страницы как на картинки."""
    content = [
        {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": base64.standard_b64encode(pdf_data).decode("utf-8"),
            },
        },
        {"type": "text", "text": prompt},
    ]
    return await ask_claude([{"role": "user", "content": content}])
