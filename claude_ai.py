from config import ANTHROPIC_API_KEY
import httpx

SYSTEM_PROMPT = """Ты умный и дружелюбный AI-ассистент в Telegram боте.
Отвечай на русском языке, если пользователь пишет по-русски.
Будь полезным, кратким и конкретным."""

async def ask_claude(messages: list) -> str:
    try:
        import anthropic
        http_client = httpx.Client()
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, http_client=http_client)
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        return f"⚠️ Ошибка: {e}"