from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command

from config import FREE_MESSAGES_PER_DAY
from database import (
    get_or_create_user, has_active_subscription,
    get_messages_today, increment_messages,
    save_message, get_history, clear_history,
    create_chat, get_active_chat_id, set_active_chat,
    get_user_chats, update_chat_title
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
        f"🆓 Free: <b>{FREE_MESSAGES_PER_DAY} messages per day</b>\n\n"
        "Use /newchat to start a new chat\n"
        "Use /chats to see your chats",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

# ─── /help ─────────────────────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📌 <b>Commands:</b>\n"
        "/start — main menu\n"
        "/newchat — start new chat\n"
        "/chats — my chats\n"
        "/status — message limit\n"
        "/clear — clear current chat\n"
        "/help — this help\n\n"
        "Just write or send a photo!",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

# ─── /newchat ──────────────────────────────────────────────────────────────

@router.message(Command("newchat"))
async def cmd_newchat(message: Message):
    user_id = message.from_user.id
    chats = await get_user_chats(user_id)
    chat_num = len(chats) + 1
    chat_id = await create_chat(user_id, f"Chat {chat_num}")
    await message.answer(
        "✨ <b>New chat started!</b>\n\n"
        "Hi! How can I help you?",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

# ─── /chats ────────────────────────────────────────────────────────────────

@router.message(Command("chats"))
async def cmd_chats(message: Message):
    user_id = message.from_user.id
    chats = await get_user_chats(user_id)
    active_chat_id = await get_active_chat_id(user_id)

    if not chats:
        await message.answer("You have no chats yet.")
        return

    buttons = []
    for chat in chats:
        mark = "✅ " if chat["id"] == active_chat_id else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{mark}{chat['title']}",
                callback_data=f"switchchat_{chat['id']}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="✨ New chat", callback_data="newchat")])

    await message.answer(
        "💬 <b>Your chats:</b>\n✅ = current chat",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

# ─── /status ───────────────────────────────────────────────────────────────

@router.message(Command("status"))
async def cmd_status(message: Message):
    await show_status(message.from_user.id, message)

# ─── /clear ────────────────────────────────────────────────────────────────

@router.message(Command("clear"))
async def cmd_clear(message: Message):
    await clear_history(message.from_user.id)
    await message.answer("🗑 Current chat history cleared!")

# ─── Callbacks ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "my_status")
async def cb_status(call: CallbackQuery):
    await show_status(call.from_user.id, call.message, edit=True)

@router.callback_query(F.data == "clear_history")
async def cb_clear(call: CallbackQuery):
    await clear_history(call.from_user.id)
    await call.answer("🗑 History cleared!", show_alert=True)

@router.callback_query(F.data == "newchat")
async def cb_newchat(call: CallbackQuery):
    user_id = call.from_user.id
    chats = await get_user_chats(user_id)
    chat_num = len(chats) + 1
    await create_chat(user_id, f"Chat {chat_num}")
    await call.message.answer(
        "✨ <b>New chat started!</b>\n\nHi! How can I help you?",
        parse_mode="HTML",
        reply_markup=main_menu()
    )
    await call.answer()

@router.callback_query(F.data.startswith("switchchat_"))
async def cb_switchchat(call: CallbackQuery):
    chat_id = int(call.data.split("_")[1])
    await set_active_chat(call.from_user.id, chat_id)
    
    chats = await get_user_chats(call.from_user.id)
    chat = next((c for c in chats if c["id"] == chat_id), None)
    title = chat["title"] if chat else "chat"
    
    await call.message.answer(
        f"✅ Switched to: <b>{title}</b>",
        parse_mode="HTML",
        reply_markup=main_menu()
    )
    await call.answer()

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

# ─── Текст ─────────────────────────────────────────────────────────────────

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

    # Автоназвание чата после первого сообщения
    chat_id = await get_active_chat_id(user_id)
    history_count = len(history)
    if history_count == 1:
        try:
            title_prompt = [{"role": "user", "content": f"Give a short 3-5 word title for a chat that starts with: '{message.text}'. Reply with title only, no quotes."}]
            title = await ask_claude(title_prompt)
            title = title.strip()[:50]
            await update_chat_title(chat_id, title)
        except:
            pass

    if not is_sub:
        await increment_messages(user_id)

    await message.answer(reply, parse_mode="HTML")

# ─── Статус ────────────────────────────────────────────────────────────────

async def show_status(user_id: int, message: Message, edit: bool = False):
    count = await get_messages_today(user_id)
    remaining = max(0, FREE_MESSAGES_PER_DAY - count)
    active_chat_id = await get_active_chat_id(user_id)
    chats = await get_user_chats(user_id)
    chat = next((c for c in chats if c["id"] == active_chat_id), None)
    chat_title = chat["title"] if chat else "Unknown"

    text = (
        f"👤 <b>Your status:</b>\n\n"
        f"💬 Messages today: {count}/{FREE_MESSAGES_PER_DAY}\n"
        f"⏳ Remaining: {remaining}\n"
        f"🗂 Current chat: {chat_title}"
    )

    if edit:
        await message.edit_text(text, parse_mode="HTML", reply_markup=main_menu())
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=main_menu())