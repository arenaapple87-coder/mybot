from config import ANTHROPIC_API_KEY
import base64

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
Be helpful, concise and friendly."""
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