from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from config import PRICES

def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Подписка", callback_data="subscription")],
        [InlineKeyboardButton(text="🗑 Очистить историю", callback_data="clear_history")],
        [InlineKeyboardButton(text="ℹ️ Мой статус", callback_data="my_status")],
    ])

def subscription_menu() -> InlineKeyboardMarkup:
    buttons = []
    for key, val in PRICES.items():
        price_usd = val["price"] / 100
        buttons.append([
            InlineKeyboardButton(
                text=f"📅 {val['label']} — ${price_usd:.2f}",
                callback_data=f"buy_{key}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_prices(plan_key: str) -> list:
    """Возвращает список LabeledPrice для Telegram Payments."""
    val = PRICES[plan_key]
    return [LabeledPrice(label=val["label"], amount=val["price"])]