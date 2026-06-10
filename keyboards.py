from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Очистить историю", callback_data="clear_history")],
        [InlineKeyboardButton(text="ℹ️ Мой статус", callback_data="my_status")],
    ])