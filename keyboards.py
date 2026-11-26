from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import PRICES
from texts import t


def main_menu(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_clear"), callback_data="clear_history")],
        [InlineKeyboardButton(text=t(lang, "btn_status"), callback_data="my_status"),
         InlineKeyboardButton(text=t(lang, "btn_subscribe"), callback_data="subscribe")],
    ])


def plans_menu(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{t(lang, 'plan_' + plan)} — {info['stars']} ⭐",
            callback_data=f"buy_{plan}",
        )]
        for plan, info in PRICES.items()
    ])
