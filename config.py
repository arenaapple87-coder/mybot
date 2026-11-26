import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Ключ Groq для распознавания голосовых (бесплатно: console.groq.com).
# Если не задан — голосовые просто отключены.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Telegram ID админов через запятую, например: 123456789,987654321
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x.isdigit()}

# Контакт для вопросов по оплате, например @username (необязательно)
SUPPORT_CONTACT = os.getenv("SUPPORT_CONTACT", "")

# ─── Лимиты ────────────────────────────────────────────────────────────────
FREE_MESSAGES_PER_DAY = 10
SUB_MESSAGES_PER_DAY = 100      # защита от слишком больших счетов за ИИ

HISTORY_MESSAGES = 10           # сколько последних сообщений чата отправлять ИИ
HISTORY_MAX_CHARS = 1500        # длинные старые сообщения обрезаются до этой длины

VOICE_MAX_MINUTES = 3
FILE_MAX_MB = 15                # Telegram даёт ботам скачивать файлы до 20 МБ
FILE_MAX_CHARS = 40000          # сколько текста из файла отправлять ИИ (~1-2 цента)
PDF_SCAN_MAX_PAGES = 5          # PDF-скан без текста читается ИИ «глазами», это дороже

# ─── Подписка (цены в звёздах Telegram ⭐) ─────────────────────────────────
PRICES = {
    "1_month":  {"stars": 150,  "days": 30},
    "3_months": {"stars": 350,  "days": 90},
    "1_year":   {"stars": 1000, "days": 365},
}
