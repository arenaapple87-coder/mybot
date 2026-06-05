from config import ANTHROPIC_API_KEY
import httpx

SYSTEM_PROMPT = """Ты умный и дружелюбный AI-ассистент в Telegram боте.
Отвечай на русском языке, если пользователь пишет по-русски.
Будь полезным, кратким и конкретным."""

async def ask_claude(messages: list) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.completions.create(
            model="claude-instant-1",
            max_tokens_to_sample=1024,
            prompt=f"\n\nHuman: {messages[-1]['content']}\n\nAssistant:",
        )
        return response.completion
    except Exception as e:
        return f"⚠️ Ошибка: {e}"