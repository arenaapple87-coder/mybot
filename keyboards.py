from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from texts import t


def main_menu(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_clear"), callback_data="clear_history")],
        [InlineKeyboardButton(text=t(lang, "btn_status"), callback_data="my_status"),
         InlineKeyboardButton(text=t(lang, "btn_subscribe"), callback_data="subscribe")],
    ])


def plans_menu(lang: str, prices: dict) -> InlineKeyboardMarkup:
    rows = []
    for plan, info in prices.items():
        text = f"{t(lang, 'plan_' + plan)} — {info['stars']} ⭐"
        if info["save"] > 0:
            text += " " + t(lang, "save", pct=info["save"])
        rows.append([InlineKeyboardButton(text=text, callback_data=f"buy_{plan}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
