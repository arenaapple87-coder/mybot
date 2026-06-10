from config import ANTHROPIC_API_KEY
import base64

SYSTEM_PROMPT = """Ты умный AI-ассистент в Telegram боте.
Отвечай на языке пользователя.
Если тебе присылают тест или задание — давай конкретный правильный ответ.
Если это вопрос с вариантами А, Б, В, Г — укажи правильный вариант и объясни почему.
Решай задачи, уравнения, переводи тексты — помогай с любыми учебными заданиями."""

async def ask_claude(messages: list) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        return f"⚠️ Ошибка: {e}"

async def ask_claude_with_image(image_data: bytes, mime_type: str, caption: str = "") -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        image_b64 = base64.standard_b64encode(image_data).decode("utf-8")
        
        content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": image_b64,
                },
            }
        ]
        
        if caption:
            content.append({"type": "text", "text": caption})
        else:
            content.append({"type": "text", "text": "Реши это задание. Если это тест с вариантами — укажи правильный ответ."})
        
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}]
        )
        return response.content[0].text
    except Exception as e:
        return f"⚠️ Ошибка: {e}"