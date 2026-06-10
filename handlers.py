from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    PreCheckoutQuery, SuccessfulPayment
)
from aiogram.filters import CommandStart, Command

from config import FREE_MESSAGES_PER_DAY
from database import (
    get_or_create_user, has_active_subscription,
    get_messages_today, increment_messages,
    save_message, get_history, clear_history,
)
from claude_ai import ask_claude, ask_claude_with_image
from keyboards import main_menu

router = Router()

# ─── /start ────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message):
    await get_or_create_user(message.from_user.id, message.from_user.username or "")
    await message.answer(
        f"👋 Hi, {message.from_user.first_name}!\n\n"
        "I am an AI assistant. Just write me something and I will answer!\n\n"
        f"🆓 Free: <b>{FREE_MESSAGES_PER_DAY} messages per day</b>",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

# ─── /help ─────────────────────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📌 <b>Commands:</b>\n"
        "/start — main menu\n"
        "/status — message limit status\n"
        "/clear — clear chat history\n"
        "/help — this help\n\n"
        "Just write or send a photo — I will answer!",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

# ─── /status ───────────────────────────────────────────────────────────────

@router.message(Command("status"))
async def cmd_status(message: Message):
    await show_status(message.from_user.id, message)

@router.message(Command("clear"))
async def cmd_clear(message: Message):
    await clear_history(message.from_user.id)
    await message.answer("🗑 Chat history cleared!")

# ─── Callback кнопки ────────────────────────────────────────────────────────

@router.callback_query(F.data == "my_status")
async def cb_status(call: CallbackQuery):
    await show_status(call.from_user.id, call.message, edit=True)

@router.callback_query(F.data == "clear_history")
async def cb_clear(call: CallbackQuery):
    await clear_history(call.from_user.id)
    await call.answer("🗑 History cleared!", show_alert=True)

# ─── Фото ──────────────────────────────────────────────────────────────────

@router.message(F.photo)
async def handle_photo(message: Message):
    user_id = message.from_user.id
    await get_or_create_user(user_id, message.from_user.username or "")

    is_sub = await has_active_subscription(user_id)
    if not is_sub:
        count = await get_messages_today(user_id)
        if count >= FREE_MESSAGES_PER_DAY:
            await message.answer(
                "⛔ Daily limit reached! Come back tomorrow.",
                reply_markup=main_menu()
            )
            return

    await message.bot.send_chat_action(message.chat.id, "typing")

    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_bytes = await message.bot.download_file(file.file_path)
    image_data = file_bytes.read()

    caption = message.caption or ""
    reply = await ask_claude_with_image(image_data, "image/jpeg", caption)

    if not is_sub:
        await increment_messages(user_id)

    await message.answer(reply, parse_mode="HTML")

# ─── Основной обработчик сообщений ─────────────────────────────────────────

@router.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    await get_or_create_user(user_id, message.from_user.username or "")

    is_sub = await has_active_subscription(user_id)

    if not is_sub:
        count = await get_messages_today(user_id)
        if count >= FREE_MESSAGES_PER_DAY:
            await message.answer(
                "⛔ Daily limit reached! Come back tomorrow.",
                reply_markup=main_menu()
            )
            return

    await message.bot.send_chat_action(message.chat.id, "typing")

    await save_message(user_id, "user", message.text)

    history = await get_history(user_id)
    reply = await ask_claude(history)

    await save_message(user_id, "assistant", reply)

    if not is_sub:
        await increment_messages(user_id)

    await message.answer(reply, parse_mode="HTML")

# ─── Вспомогательные функции ───────────────────────────────────────────────

async def show_status(user_id: int, message: Message, edit: bool = False):
    import aiosqlite
    from database import DB_PATH
    from datetime import datetime

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT sub_expires FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()

    count = await get_messages_today(user_id)
    remaining = max(0, FREE_MESSAGES_PER_DAY - count)

    text = (
        f"👤 <b>Your status:</b>\n\n"
        f"💬 Messages today: {count}/{FREE_MESSAGES_PER_DAY}\n"
        f"⏳ Remaining: {remaining}"
    )

    if edit:
        await message.edit_text(text, parse_mode="HTML", reply_markup=main_menu())
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=main_menu())