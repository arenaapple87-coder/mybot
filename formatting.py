import html
import re

TELEGRAM_LIMIT = 4000  # у Telegram лимит 4096 символов, оставляем запас


def md_to_html(text: str) -> str:
    """Превращает Markdown из ответа ИИ в безопасный HTML для Telegram.
    Символы < > & экранируются, поэтому Telegram больше не отклоняет ответ."""
    blocks = []

    def keep_block(m):
        blocks.append(f"<pre>{html.escape(m.group(1).strip())}</pre>")
        return f"\x00{len(blocks) - 1}\x00"

    # блоки кода ```...```
    text = re.sub(r"```[\w+-]*\n?(.*?)```", keep_block, text, flags=re.S)
    text = html.escape(text, quote=False)

    text = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text, flags=re.S)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text, flags=re.S)
    text = re.sub(r"^#{1,6}\s*(.+)$", r"<b>\1</b>", text, flags=re.M)
    text = re.sub(r"^(\s*)[-*]\s+", r"\1• ", text, flags=re.M)

    return re.sub(r"\x00(\d+)\x00", lambda m: blocks[int(m.group(1))], text)


def split_text(text: str, limit: int = TELEGRAM_LIMIT) -> list:
    """Режет длинный текст на части, стараясь резать по абзацам и строкам."""
    parts = []
    while len(text) > limit:
        cut = text.rfind("\n\n", 0, limit)
        if cut < limit // 2:
            cut = text.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = text.rfind(" ", 0, limit)
        if cut <= 0:
            cut = limit
        parts.append(text[:cut])
        text = text[cut:].lstrip()
    if text:
        parts.append(text)
    return parts


async def send_long(message, text: str, reply_markup=None):
    """Отправляет ответ ИИ: красиво оформленным, частями, если он длинный.
    Если оформление вдруг не принято Telegram, отправляет обычным текстом."""
    parts = split_text(text)
    for i, part in enumerate(parts):
        markup = reply_markup if i == len(parts) - 1 else None
        try:
            await message.answer(md_to_html(part), parse_mode="HTML", reply_markup=markup)
        except Exception:
            await message.answer(part, reply_markup=markup)
