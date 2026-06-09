import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")

FREE_MESSAGES_PER_DAY = 12

PRICES = {
    "1_month":  {"label": "1 месяц",  "price": 2.99,  "days": 30},
    "3_months": {"label": "3 месяца", "price": 5.99,  "days": 90},
    "1_year":   {"label": "1 год",    "price": 12.99, "days": 365},
}

CURRENCY = "USD"