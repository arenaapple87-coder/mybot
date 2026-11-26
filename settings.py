"""Настройки, которые админ меняет прямо в боте (хранятся в базе)."""
from config import FREE_MESSAGES_PER_DAY, SUB_MESSAGES_PER_DAY, MONTH_PRICE, PLANS
from database import get_setting

DEFAULTS = {
    "free_limit": FREE_MESSAGES_PER_DAY,
    "sub_limit": SUB_MESSAGES_PER_DAY,
    "month_price": MONTH_PRICE,
}


async def get_int(key: str) -> int:
    value = await get_setting(key)
    return int(value) if value is not None else DEFAULTS[key]


async def free_limit() -> int:
    return await get_int("free_limit")


async def sub_limit() -> int:
    return await get_int("sub_limit")


async def get_prices() -> dict:
    """{план: {"stars": цена, "days": дней, "save": выгода в %}}"""
    month = await get_int("month_price")
    prices = {}
    for plan, info in PLANS.items():
        stars = int(round(month * info["pay_months"] / 5) * 5)  # круглые числа
        full = month * info["months"]
        prices[plan] = {
            "stars": stars,
            "days": info["days"],
            "save": round((1 - stars / full) * 100) if full else 0,
        }
    return prices
