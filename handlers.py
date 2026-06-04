from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    PreCheckoutQuery, SuccessfulPayment
)
from aiogram.filters import CommandStart, Command

from config import FREE_MESSAGES_PER_DAY, PRICES, PAYMENT_PROVIDER_TOKEN, CURRENCY
from database import (
    get_or_create_user, has_active_subscription,
    get_messages_today, increment_messages,
    save_message, get_history, clear_history,
    add_subscription
)
from claude_ai import ask_claude
from keyboards import main_menu, subscription_menu, get_prices

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await get_or_create_user(message.from_user.id, message.from_user.username or "")
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я AI-ассистент на базе Claude. Просто напиши мне что-нибудь!\n\n"
        f"🆓 Бесплатно: <b>{FREE_MESSAGES_PER_DAY} сообщений в день</b>\n"
        "💎 С подпиской: <b>безлимитно</b>",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📌 <b>Команды:</b>\n"
        "/start — главное меню\n"
        "/status — статус подписки\n"
        "/clear — очистить историю\n"
        "/help — справка",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

@router.message(Command("status"))
async def cmd_status(message: Message):
    await show_status(message.from_user.id, message)

@router.message(Command("clear"))
async def cmd_clear(message: Message):
    await clear_history(message.from_user.id)
    await message.answer("🗑 История диалога очищена!")

@router.callback_query(F.data == "subscription")
async def cb_subscription(call: CallbackQuery):
    is_sub = await has_active_subscription(call.from_user.id)
    prefix = "✅ У тебя активна подписка!\n\n" if is_sub else ""
    await call.message.edit_text(
        f"{prefix}💎 <b>Выбери план подписки:</b>\n\n"
        "С подпиской ты получаешь:\n"
        "• Безлимитные сообщения\n"
        "• Полная история диалога",
        reply_markup=subscription_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "my_status")
async def cb_status(call: CallbackQuery):
    await show_status(call.from_user.id, call.message, edit=True)

@router.callback_query(F.data == "clear_history")
async def cb_clear(call: CallbackQuery):
    await clear_history(call.from_user.id)
    await call.answer("🗑 История очищена!", show_alert=True)

@router.callback_query(F.data == "back_main")
async def cb_back(call: CallbackQuery):
    await call.message.edit_text("Главное меню 👇", reply_markup=main_menu())

@router.callback_query(F.data.startswith("buy_"))
async def cb_buy(call: CallbackQuery):
    plan_key = call.data[4:]
    if plan_key not in PRICES:
        await call.answer("Неизвестный план", show_alert=True)
        return
    plan = PRICES[plan_key]
    await call.message.answer_invoice(
        title=f"Подписка на {plan['label']}",
        description=f"Безлимитные запросы к AI на {plan['label']}",
        payload=plan_key,
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency=CURRENCY,
        prices=get_prices(plan_key),
        start_parameter=f"sub_{plan_key}"
    )
    await call.answer()

@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)

@router.message(F.successful_payment)
async def payment_done(message: Message):
    plan_key = message.successful_payment.invoice_payload
    if plan_key not in PRICES:
        await message.answer("⚠️ Ошибка: неизвестный план.")
        return
    plan = PRICES[plan_key]
    expires = await add_subscription(message.from_user.id, plan["days"])
    await message.answer(
        f"🎉 <b>Оплата прошла!</b>\n\n"
        f"✅ Подписка: <b>{plan['label']}</b>\n"
        f"📅 До: <b>{expires.strftime('%d.%m.%Y')}</b>",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

@router.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    await get_or_create_user(user_id, message.from_user.username or "")
    is_sub = await has_active_subscription(user_id)

    if not is_sub:
        count = await get_messages_today(user_id)
        if count >= FREE_MESSAGES_PER_DAY:
            await message.answer(
                f"⛔ <b>Лимит исчерпан!</b>\n\n"
                f"Бесплатно: <b>{FREE_MESSAGES_PER_DAY} сообщений в день</b>.\n"
                "Лимит обновится завтра.\n\n"
                "💎 Оформи подписку:",
                parse_mode="HTML",
                reply_markup=subscription_menu()
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

async def show_status(user_id: int, message: Message, edit: bool = False):
    is_sub = await has_active_subscription(user_id)
    from database import DB_PATH
    import aiosqlite
    from datetime import datetime

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT sub_expires FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()

    if is_sub and row and row[0]:
        expires = datetime.fromisoformat(row[0])
        sub_text = f"✅ <b>Активна</b> до {expires.strftime('%d.%m.%Y')}"
    else:
        sub_text = "❌ <b>Нет подписки</b>"

    count = await get_messages_today(user_id)
    remaining = max(0, FREE_MESSAGES_PER_DAY - count)

    text = (
        f"👤 <b>Твой статус:</b>\n\n"
        f"💎 Подписка: {sub_text}\n"
        f"💬 Сообщений сегодня: {count}/{FREE_MESSAGES_PER_DAY}\n"
        f"⏳ Осталось: {remaining if not is_sub else '∞'}"
    )

    if edit:
        await message.edit_text(text, parse_mode="HTML", reply_markup=main_menu())
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=main_menu())