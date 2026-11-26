import html

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery,
)

from config import (
    ADMIN_IDS, PLANS, SUPPORT_CONTACT,
    HISTORY_MESSAGES, VOICE_MAX_MINUTES, FILE_MAX_MB, FILE_MAX_CHARS, PDF_SCAN_MAX_PAGES,
)
from database import (
    get_or_create_user, get_sub_expires, extend_subscription,
    get_messages_today, increment_messages,
    save_message, get_history, clear_history,
    create_chat, get_active_chat_id, set_active_chat,
    get_user_chats, update_chat_title,
    touch_user, get_stats, set_setting,
)
import settings
from claude_ai import ask_claude, ask_claude_with_image, ask_claude_with_pdf, AIError
from formatting import send_long
from keyboards import main_menu, plans_menu
from texts import t, get_lang
import files
import voice

router = Router()


def fmt_date(dt) -> str:
    return dt.strftime("%d.%m.%Y")


# ─── Лимиты ────────────────────────────────────────────────────────────────

async def check_limit(message: Message, lang: str) -> bool:
    """Регистрирует пользователя и проверяет дневной лимит. True — можно отвечать."""
    user = message.from_user
    await get_or_create_user(user.id, user.username or "")
    is_sub = await get_sub_expires(user.id) is not None
    limit = await settings.sub_limit() if is_sub else await settings.free_limit()
    if await get_messages_today(user.id) >= limit:
        if is_sub:
            await message.answer(t(lang, "limit_sub", limit=limit))
        else:
            await message.answer(t(lang, "limit_free"), reply_markup=plans_menu(lang, await settings.get_prices()))
        return False
    return True


async def count_message(user_id: int):
    await touch_user(user_id)
    await increment_messages(user_id)


# ─── /start, /help ─────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message):
    lang = get_lang(message.from_user)
    await get_or_create_user(message.from_user.id, message.from_user.username or "")
    await message.answer(
        t(lang, "start", name=html.escape(message.from_user.first_name or ""), free=await settings.free_limit()),
        reply_markup=main_menu(lang),
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    lang = get_lang(message.from_user)
    await message.answer(t(lang, "help"), parse_mode="HTML", reply_markup=main_menu(lang))


# ─── Чаты ──────────────────────────────────────────────────────────────────

async def start_new_chat(user, target: Message):
    lang = get_lang(user)
    await get_or_create_user(user.id, user.username or "")
    chats = await get_user_chats(user.id)
    await create_chat(user.id, t(lang, "chat_default_title", n=len(chats) + 1))
    await target.answer(t(lang, "new_chat"), parse_mode="HTML", reply_markup=main_menu(lang))


@router.message(Command("newchat"))
async def cmd_newchat(message: Message):
    await start_new_chat(message.from_user, message)


@router.callback_query(F.data == "newchat")
async def cb_newchat(call: CallbackQuery):
    await start_new_chat(call.from_user, call.message)
    await call.answer()


@router.message(Command("chats"))
async def cmd_chats(message: Message):
    lang = get_lang(message.from_user)
    user_id = message.from_user.id
    chats = await get_user_chats(user_id)
    active_chat_id = await get_active_chat_id(user_id)

    if not chats:
        await message.answer(t(lang, "no_chats"))
        return

    buttons = [
        [InlineKeyboardButton(
            text=("✅ " if chat["id"] == active_chat_id else "") + chat["title"],
            callback_data=f"switchchat_{chat['id']}",
        )]
        for chat in chats
    ]
    buttons.append([InlineKeyboardButton(text=t(lang, "btn_new_chat"), callback_data="newchat")])
    await message.answer(
        t(lang, "your_chats"), parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("switchchat_"))
async def cb_switchchat(call: CallbackQuery):
    lang = get_lang(call.from_user)
    chat_id = int(call.data.split("_")[1])
    chats = await get_user_chats(call.from_user.id)
    chat = next((c for c in chats if c["id"] == chat_id), None)
    if chat is None:  # чужой или удалённый чат
        await call.answer()
        return
    await set_active_chat(call.from_user.id, chat_id)
    await call.message.answer(
        t(lang, "switched", title=html.escape(chat["title"])),
        parse_mode="HTML", reply_markup=main_menu(lang),
    )
    await call.answer()


@router.message(Command("clear"))
async def cmd_clear(message: Message):
    await clear_history(message.from_user.id)
    await message.answer(t(get_lang(message.from_user), "cleared"))


@router.callback_query(F.data == "clear_history")
async def cb_clear(call: CallbackQuery):
    await clear_history(call.from_user.id)
    await call.answer(t(get_lang(call.from_user), "alert_cleared"), show_alert=True)


# ─── Статус ────────────────────────────────────────────────────────────────

async def status_text(user) -> str:
    lang = get_lang(user)
    await get_or_create_user(user.id, user.username or "")
    expires = await get_sub_expires(user.id)
    limit = await settings.sub_limit() if expires else await settings.free_limit()
    count = await get_messages_today(user.id)
    active_chat_id = await get_active_chat_id(user.id)
    chats = await get_user_chats(user.id)
    chat = next((c for c in chats if c["id"] == active_chat_id), None)
    return t(
        lang, "status",
        plan=t(lang, "plan_sub", date=fmt_date(expires)) if expires else t(lang, "plan_free"),
        count=count, limit=limit, remaining=max(0, limit - count),
        chat=html.escape(chat["title"]) if chat else t(lang, "unknown_chat"),
    )


@router.message(Command("status"))
async def cmd_status(message: Message):
    lang = get_lang(message.from_user)
    await message.answer(await status_text(message.from_user), parse_mode="HTML", reply_markup=main_menu(lang))


@router.callback_query(F.data == "my_status")
async def cb_status(call: CallbackQuery):
    lang = get_lang(call.from_user)
    try:
        await call.message.edit_text(await status_text(call.from_user), parse_mode="HTML", reply_markup=main_menu(lang))
    except Exception:
        pass  # текст не изменился — Telegram не даёт «редактировать» на то же самое
    await call.answer()


# ─── /stats (только для админа) ────────────────────────────────────────────

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await message.answer(
            f"⛔ Эта команда только для админа.\n\nТвой Telegram ID: <code>{user_id}</code>",
            parse_mode="HTML",
        )
        return

    s = await get_stats()
    await message.answer(
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{s['users_total']}</b>\n"
        f"🆕 Новых сегодня: {s['users_new_today']}\n"
        f"🆕 Новых за 7 дней: {s['users_new_week']}\n\n"
        f"🔥 Активных сегодня: <b>{s['active_today']}</b>\n"
        f"📅 Активных за 7 дней: {s['active_week']}\n"
        f"🗓 Активных за 30 дней: {s['active_month']}\n\n"
        f"💬 Сообщений сегодня: {s['msgs_today']}\n"
        f"💬 Ответов ИИ всего: {s['msgs_total']}\n\n"
        f"⭐ Активных подписок: {s['subscribers']}\n"
        f"⭐ Заработано звёзд за 30 дней: {s['stars_month']}\n"
        f"⭐ Заработано звёзд всего: {s['stars_total']}\n\n"
        "<i>Время по UTC. «Активный» — получил хотя бы один ответ от ИИ.</i>\n⚙️ Цены и лимиты: /admin",
        parse_mode="HTML",
    )


# ─── Настройки цен и лимитов (только для админа) ───────────────────────────

async def admin_text() -> str:
    prices = await settings.get_prices()
    lines = [
        "⚙️ <b>Настройки бота</b>\n",
        f"🆓 Бесплатно в день: <b>{await settings.free_limit()}</b> сообщений",
        f"⭐ Подписчикам в день: <b>{await settings.sub_limit()}</b> сообщений\n",
        "💰 <b>Цены:</b>",
    ]
    names = {"1_month": "1 месяц", "3_months": "3 месяца", "1_year": "1 год"}
    for plan, info in prices.items():
        extra = f" (выгода {info['save']}%)" if info["save"] else ""
        lines.append(f"• {names[plan]}: {info['stars']} ⭐ ≈ ${info['stars'] * 0.013:.2f} тебе{extra}")
    lines += [
        "\n<b>Команды:</b>",
        "<code>/setprice 300</code> — цена месяца (3 мес. и год посчитаются сами)",
        "<code>/setlimit free 5</code> — бесплатный лимит в день",
        "<code>/setlimit sub 30</code> — лимит подписчиков в день",
    ]
    return "\n".join(lines)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer(await admin_text(), parse_mode="HTML")


@router.message(Command("setprice"))
async def cmd_setprice(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit() or not 1 <= int(parts[1]) <= 10000:
        await message.answer("Напиши так: <code>/setprice 300</code> (от 1 до 10000 ⭐)", parse_mode="HTML")
        return
    await set_setting("month_price", int(parts[1]))
    await message.answer("✅ Готово!\n\n" + await admin_text(), parse_mode="HTML")


@router.message(Command("setlimit"))
async def cmd_setlimit(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = (message.text or "").split()
    keys = {"free": "free_limit", "sub": "sub_limit"}
    if len(parts) != 3 or parts[1] not in keys or not parts[2].isdigit() or not 0 <= int(parts[2]) <= 1000:
        await message.answer(
            "Напиши так: <code>/setlimit free 5</code> или <code>/setlimit sub 30</code>", parse_mode="HTML")
        return
    await set_setting(keys[parts[1]], int(parts[2]))
    await message.answer("✅ Готово!\n\n" + await admin_text(), parse_mode="HTML")


# ─── Подписка (Telegram Stars) ─────────────────────────────────────────────

async def show_plans(user, target: Message):
    lang = get_lang(user)
    await get_or_create_user(user.id, user.username or "")
    text = t(lang, "subscribe", limit=await settings.sub_limit(), free=await settings.free_limit())
    expires = await get_sub_expires(user.id)
    if expires:
        text += t(lang, "sub_active_until", date=fmt_date(expires))
    await target.answer(text, parse_mode="HTML", reply_markup=plans_menu(lang, await settings.get_prices()))


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    await show_plans(message.from_user, message)


@router.callback_query(F.data == "subscribe")
async def cb_subscribe(call: CallbackQuery):
    await show_plans(call.from_user, call.message)
    await call.answer()


@router.callback_query(F.data.startswith("buy_"))
async def cb_buy(call: CallbackQuery):
    lang = get_lang(call.from_user)
    plan = call.data[len("buy_"):]
    prices = await settings.get_prices()
    if plan not in prices:
        await call.answer()
        return
    period = t(lang, "plan_" + plan)
    stars = prices[plan]["stars"]
    await call.message.answer_invoice(
        title=t(lang, "invoice_title", period=period),
        description=t(lang, "invoice_desc", limit=await settings.sub_limit(), period=period),
        payload=f"sub:{plan}:{stars}",  # цена в счёте фиксируется, даже если админ её потом поменяет
        provider_token="",  # для звёзд Telegram токен не нужен
        currency="XTR",
        prices=[LabeledPrice(label=period, amount=stars)],
    )
    await call.answer()


def parse_payload(payload: str):
    """'sub:1_month:150' -> ('1_month', 150)"""
    parts = payload.split(":")
    plan = parts[1] if len(parts) > 1 else ""
    stars = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else -1
    return plan, stars


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    plan, stars = parse_payload(query.invoice_payload)
    ok = plan in PLANS and query.currency == "XTR" and query.total_amount == stars
    await query.answer(ok=ok, error_message=None if ok else "Plan not found, please try again: /subscribe")


@router.message(F.successful_payment)
async def on_paid(message: Message):
    lang = get_lang(message.from_user)
    payment = message.successful_payment
    plan, _ = parse_payload(payment.invoice_payload)
    days = PLANS.get(plan, {}).get("days", 30)
    await get_or_create_user(message.from_user.id, message.from_user.username or "")
    expires = await extend_subscription(
        message.from_user.id, days, plan, payment.total_amount, payment.telegram_payment_charge_id,
    )
    await message.answer(t(lang, "paid", date=fmt_date(expires)), parse_mode="HTML", reply_markup=main_menu(lang))


@router.message(Command("paysupport"))
async def cmd_paysupport(message: Message):
    lang = get_lang(message.from_user)
    contact = f": {SUPPORT_CONTACT}" if SUPPORT_CONTACT else ""
    await message.answer(t(lang, "paysupport", contact=html.escape(contact)))


# ─── Общий ответ на текст (обычный, из голосового или из файла) ────────────

async def answer_text(message: Message, lang: str, user_text: str, history_note: str | None = None):
    """Отправляет текст ИИ с историей чата и сохраняет диалог.
    history_note — что записать в историю вместо user_text (для больших файлов)."""
    user_id = message.from_user.id
    history = await get_history(user_id, limit=HISTORY_MESSAGES)
    is_first_message = len(history) == 0
    history.append({"role": "user", "content": user_text})

    try:
        reply = await ask_claude(history)
    except AIError:
        await message.answer(t(lang, "ai_error"))
        return None

    await save_message(user_id, "user", history_note or user_text)
    await save_message(user_id, "assistant", reply)
    await count_message(user_id)
    await send_long(message, reply)

    if is_first_message:
        await auto_title(user_id, history_note or user_text)
    return reply


async def auto_title(user_id: int, first_text: str):
    try:
        chat_id = await get_active_chat_id(user_id)
        prompt = [{"role": "user", "content":
                   f"Give a short 3-5 word title for a chat that starts with: '{first_text[:500]}'. "
                   "Use the same language. Reply with the title only, no quotes, no formatting."}]
        title = await ask_claude(prompt, max_tokens=30)
        await update_chat_title(chat_id, title.strip().strip('"*«»')[:50])
    except Exception:
        pass


# ─── Фото ──────────────────────────────────────────────────────────────────

async def answer_image(message: Message, lang: str, image_data: bytes, mime: str):
    prompt = message.caption or t(lang, "solve_image")
    try:
        reply = await ask_claude_with_image(image_data, mime, prompt)
    except AIError:
        await message.answer(t(lang, "ai_error"))
        return
    await save_message(message.from_user.id, "user", "🖼 " + prompt)
    await save_message(message.from_user.id, "assistant", reply)
    await count_message(message.from_user.id)
    await send_long(message, reply)


async def download(message: Message, file_id: str) -> bytes:
    file = await message.bot.get_file(file_id)
    data = await message.bot.download_file(file.file_path)
    return data.read()


@router.message(F.photo)
async def handle_photo(message: Message):
    lang = get_lang(message.from_user)
    if not await check_limit(message, lang):
        return
    await message.bot.send_chat_action(message.chat.id, "typing")
    image_data = await download(message, message.photo[-1].file_id)
    await answer_image(message, lang, image_data, "image/jpeg")


# ─── Голосовые ─────────────────────────────────────────────────────────────

@router.message(F.voice | F.audio)
async def handle_voice(message: Message):
    lang = get_lang(message.from_user)
    if not voice.voice_enabled():
        await message.answer(t(lang, "voice_off"))
        return
    media = message.voice or message.audio
    if (media.duration or 0) > VOICE_MAX_MINUTES * 60:
        await message.answer(t(lang, "voice_too_long", max=VOICE_MAX_MINUTES))
        return
    if not await check_limit(message, lang):
        return

    await message.bot.send_chat_action(message.chat.id, "typing")
    audio = await download(message, media.file_id)
    text = await voice.transcribe(audio, getattr(media, "file_name", None) or "voice.ogg")
    if not text:
        await message.answer(t(lang, "voice_failed"))
        return

    await message.answer(t(lang, "voice_heard", text=html.escape(text[:1000])), parse_mode="HTML")
    await answer_text(message, lang, text)


# ─── Файлы ─────────────────────────────────────────────────────────────────

@router.message(F.document)
async def handle_document(message: Message):
    lang = get_lang(message.from_user)
    doc = message.document
    kind = files.kind_of(doc.file_name, doc.mime_type)
    if not kind:
        await message.answer(t(lang, "file_unsupported"))
        return
    if (doc.file_size or 0) > FILE_MAX_MB * 1024 * 1024:
        await message.answer(t(lang, "file_too_big", max=FILE_MAX_MB))
        return
    if not await check_limit(message, lang):
        return

    await message.bot.send_chat_action(message.chat.id, "typing")
    data = await download(message, doc.file_id)

    if kind == "image":
        await answer_image(message, lang, data, doc.mime_type)
        return

    task = message.caption or t(lang, "file_default_task")
    name = doc.file_name or "file"
    try:
        if kind == "pdf":
            text, pages = files.pdf_text(data)
        elif kind == "docx":
            text, pages = files.docx_text(data), 0
        else:
            text, pages = files.txt_text(data), 0
    except Exception:
        text, pages = "", 0

    # PDF-скан без текста: даём ИИ посмотреть на страницы, если их немного
    if not text and kind == "pdf" and 0 < pages <= PDF_SCAN_MAX_PAGES:
        try:
            reply = await ask_claude_with_pdf(data, task)
        except AIError:
            await message.answer(t(lang, "ai_error"))
            return
        await save_message(message.from_user.id, "user", f"📄 {name}: {task}")
        await save_message(message.from_user.id, "assistant", reply)
        await count_message(message.from_user.id)
        await send_long(message, reply)
        return

    if not text:
        await message.answer(t(lang, "file_empty"))
        return

    was_cut = len(text) > FILE_MAX_CHARS
    prompt = f"File «{name}»:\n\n{text[:FILE_MAX_CHARS]}\n\n---\n{task}"
    reply = await answer_text(message, lang, prompt, history_note=f"📄 {name}: {task}")
    if reply is not None and was_cut:
        await message.answer(t(lang, "file_cut").strip(), parse_mode="HTML")


# ─── Текст ─────────────────────────────────────────────────────────────────

@router.message(F.text)
async def handle_message(message: Message):
    lang = get_lang(message.from_user)
    if not await check_limit(message, lang):
        return
    await message.bot.send_chat_action(message.chat.id, "typing")
    await answer_text(message, lang, message.text)
