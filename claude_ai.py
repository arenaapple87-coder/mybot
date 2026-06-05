from config import ANTHROPIC_API_KEY

SYSTEM_PROMPT = """Ты умный и дружелюбный AI-ассистент в Telegram боте.
Отвечай на русском языке, если пользователь пишет по-русски.
Будь полезным, кратким и конкретным."""

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