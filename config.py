import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Распознавание голосовых: нужен один из ключей (если нет ни одного — голосовые выключены).
# OpenAI: platform.openai.com (платно, меньше цента за минуту)
# Groq:   console.groq.com (бесплатно, но доступен не во всех странах)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Telegram ID админов через запятую, например: 123456789,987654321
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x.isdigit()}

# Контакт для вопросов по оплате, например @username (необязательно)
SUPPORT_CONTACT = os.getenv("SUPPORT_CONTACT", "")

# ─── Лимиты ────────────────────────────────────────────────────────────────
# Значения по умолчанию. Админ меняет их прямо в боте: /admin
FREE_MESSAGES_PER_DAY = 5
SUB_MESSAGES_PER_DAY = 30       # защита от слишком больших счетов за ИИ

HISTORY_MESSAGES = 10           # сколько последних сообщений чата отправлять ИИ
HISTORY_MAX_CHARS = 1500        # длинные старые сообщения обрезаются до этой длины

VOICE_MAX_MINUTES = 3
FILE_MAX_MB = 15                # Telegram даёт ботам скачивать файлы до 20 МБ
FILE_MAX_CHARS = 40000          # сколько текста из файла отправлять ИИ (~1-2 цента)
PDF_SCAN_MAX_PAGES = 5          # PDF-скан без текста читается ИИ «глазами», это дороже

# ─── Подписка (цены в звёздах Telegram ⭐) ─────────────────────────────────
# Админ задаёт только цену месяца (/setprice), остальное считается само:
# 3 месяца = 2.5 месяца (выгода 17%), год = 8 месяцев (выгода 33%).
MONTH_PRICE = 150
PLANS = {
    "1_month":  {"days": 30,  "months": 1,  "pay_months": 1},
    "3_months": {"days": 90,  "months": 3,  "pay_months": 2.5},
    "1_year":   {"days": 365, "months": 12, "pay_months": 8},
}

# ─── Промокоды: КОД -> сколько дней подписки даёт. Каждый человек — один раз. ──
PROMO_CODES = {
    "LYDMILA": 7,
}
