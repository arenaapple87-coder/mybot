"""Все тексты бота на трёх языках. Язык выбирается по настройкам Telegram пользователя."""

LANGS = ("ru", "uk", "en")


def get_lang(user) -> str:
    code = (getattr(user, "language_code", None) or "").lower()[:2]
    if code in LANGS:
        return code
    if code in ("be", "kk", "ky", "uz", "tg", "az", "hy", "ka"):
        return "ru"
    return "en"


TEXTS = {
    "start": {
        "ru": "👋 Привет, {name}!\n\nЯ ИИ-помощник. Пиши вопрос, отправляй фото, голосовое или файл (PDF, Word, TXT), и я отвечу!\n\n🆓 Бесплатно: <b>{free} сообщений в день</b>\n⭐ Подписка: /subscribe\n\n/newchat — новый чат\n/chats — мои чаты",
        "uk": "👋 Привіт, {name}!\n\nЯ ШІ-помічник. Пиши питання, надсилай фото, голосове або файл (PDF, Word, TXT), і я відповім!\n\n🆓 Безкоштовно: <b>{free} повідомлень на день</b>\n⭐ Підписка: /subscribe\n\n/newchat — новий чат\n/chats — мої чати",
        "en": "👋 Hi, {name}!\n\nI'm an AI assistant. Write a question, send a photo, a voice message or a file (PDF, Word, TXT), and I'll answer!\n\n🆓 Free: <b>{free} messages per day</b>\n⭐ Subscription: /subscribe\n\n/newchat — new chat\n/chats — my chats",
    },
    "help": {
        "ru": "📌 <b>Команды:</b>\n/start — главное меню\n/newchat — новый чат\n/chats — мои чаты\n/status — мой лимит\n/clear — очистить текущий чат\n/subscribe — подписка ⭐\n/help — помощь\n\nМожно писать текст, отправлять фото, голосовые и файлы (PDF, Word, TXT).",
        "uk": "📌 <b>Команди:</b>\n/start — головне меню\n/newchat — новий чат\n/chats — мої чати\n/status — мій ліміт\n/clear — очистити поточний чат\n/subscribe — підписка ⭐\n/help — допомога\n\nМожна писати текст, надсилати фото, голосові та файли (PDF, Word, TXT).",
        "en": "📌 <b>Commands:</b>\n/start — main menu\n/newchat — new chat\n/chats — my chats\n/status — my limit\n/clear — clear current chat\n/subscribe — subscription ⭐\n/help — help\n\nYou can send text, photos, voice messages and files (PDF, Word, TXT).",
    },
    "new_chat": {
        "ru": "━━━━━━━━━━━━━━━━━━━\n✨ <b>Новый чат начат!</b>\n━━━━━━━━━━━━━━━━━━━\n\nПривет! Чем помочь?",
        "uk": "━━━━━━━━━━━━━━━━━━━\n✨ <b>Новий чат розпочато!</b>\n━━━━━━━━━━━━━━━━━━━\n\nПривіт! Чим допомогти?",
        "en": "━━━━━━━━━━━━━━━━━━━\n✨ <b>New chat started!</b>\n━━━━━━━━━━━━━━━━━━━\n\nHi! How can I help you?",
    },
    "switched": {
        "ru": "━━━━━━━━━━━━━━━━━━━\n💬 Переключено на: <b>{title}</b>\n━━━━━━━━━━━━━━━━━━━\n\nЧем помочь?",
        "uk": "━━━━━━━━━━━━━━━━━━━\n💬 Перемкнено на: <b>{title}</b>\n━━━━━━━━━━━━━━━━━━━\n\nЧим допомогти?",
        "en": "━━━━━━━━━━━━━━━━━━━\n💬 Switched to: <b>{title}</b>\n━━━━━━━━━━━━━━━━━━━\n\nHow can I help you?",
    },
    "chat_default_title": {"ru": "Чат {n}", "uk": "Чат {n}", "en": "Chat {n}"},
    "no_chats": {"ru": "У тебя пока нет чатов.", "uk": "У тебе поки немає чатів.", "en": "You have no chats yet."},
    "your_chats": {
        "ru": "💬 <b>Твои чаты:</b>\n✅ = текущий чат",
        "uk": "💬 <b>Твої чати:</b>\n✅ = поточний чат",
        "en": "💬 <b>Your chats:</b>\n✅ = current chat",
    },
    "cleared": {
        "ru": "🗑 История текущего чата очищена!",
        "uk": "🗑 Історію поточного чату очищено!",
        "en": "🗑 Current chat history cleared!",
    },
    "limit_free": {
        "ru": "⛔ Бесплатный лимит на сегодня закончился. Возвращайся завтра или оформи подписку: /subscribe",
        "uk": "⛔ Безкоштовний ліміт на сьогодні закінчився. Повертайся завтра або оформи підписку: /subscribe",
        "en": "⛔ Today's free limit is used up. Come back tomorrow or subscribe: /subscribe",
    },
    "limit_sub": {
        "ru": "⛔ Дневной лимит ({limit} сообщений) исчерпан. Он обновится завтра.",
        "uk": "⛔ Денний ліміт ({limit} повідомлень) вичерпано. Він оновиться завтра.",
        "en": "⛔ Daily limit ({limit} messages) reached. It resets tomorrow.",
    },
    "status": {
        "ru": "👤 <b>Твой статус:</b>\n\n{plan}\n💬 Сообщений сегодня: {count}/{limit}\n⏳ Осталось: {remaining}\n🗂 Текущий чат: {chat}",
        "uk": "👤 <b>Твій статус:</b>\n\n{plan}\n💬 Повідомлень сьогодні: {count}/{limit}\n⏳ Залишилось: {remaining}\n🗂 Поточний чат: {chat}",
        "en": "👤 <b>Your status:</b>\n\n{plan}\n💬 Messages today: {count}/{limit}\n⏳ Remaining: {remaining}\n🗂 Current chat: {chat}",
    },
    "plan_free": {"ru": "🆓 Тариф: бесплатный", "uk": "🆓 Тариф: безкоштовний", "en": "🆓 Plan: free"},
    "plan_sub": {
        "ru": "⭐ Подписка до {date}",
        "uk": "⭐ Підписка до {date}",
        "en": "⭐ Subscribed until {date}",
    },
    "unknown_chat": {"ru": "—", "uk": "—", "en": "—"},
    "ai_error": {
        "ru": "⚠️ Не получилось получить ответ. Попробуй ещё раз через минуту.",
        "uk": "⚠️ Не вдалося отримати відповідь. Спробуй ще раз за хвилину.",
        "en": "⚠️ Couldn't get an answer. Please try again in a minute.",
    },
    "solve_image": {
        "ru": "Реши это задание. Если это тест с вариантами — укажи правильный ответ.",
        "uk": "Розв'яжи це завдання. Якщо це тест з варіантами — вкажи правильну відповідь.",
        "en": "Solve this task. If it's a multiple choice test, give the correct answer.",
    },
    # ─── Голосовые ───
    "voice_off": {
        "ru": "🎤 Голосовые сообщения пока не подключены. Напиши, пожалуйста, текстом.",
        "uk": "🎤 Голосові повідомлення поки не підключені. Напиши, будь ласка, текстом.",
        "en": "🎤 Voice messages aren't enabled yet. Please type your message.",
    },
    "voice_too_long": {
        "ru": "🎤 Голосовое слишком длинное. Максимум: {max} мин.",
        "uk": "🎤 Голосове занадто довге. Максимум: {max} хв.",
        "en": "🎤 The voice message is too long. Maximum: {max} min.",
    },
    "voice_failed": {
        "ru": "🎤 Не получилось распознать голосовое. Попробуй ещё раз или напиши текстом.",
        "uk": "🎤 Не вдалося розпізнати голосове. Спробуй ще раз або напиши текстом.",
        "en": "🎤 Couldn't recognize the voice message. Try again or type it.",
    },
    "voice_heard": {"ru": "🎤 <i>{text}</i>", "uk": "🎤 <i>{text}</i>", "en": "🎤 <i>{text}</i>"},
    # ─── Файлы ───
    "file_too_big": {
        "ru": "📄 Файл слишком большой. Максимум: {max} МБ.",
        "uk": "📄 Файл занадто великий. Максимум: {max} МБ.",
        "en": "📄 The file is too big. Maximum: {max} MB.",
    },
    "file_unsupported": {
        "ru": "📄 Такой формат я пока не читаю. Поддерживаются: PDF, Word (.docx), TXT и картинки.",
        "uk": "📄 Такий формат я поки не читаю. Підтримуються: PDF, Word (.docx), TXT і зображення.",
        "en": "📄 I can't read this format yet. Supported: PDF, Word (.docx), TXT and images.",
    },
    "file_empty": {
        "ru": "📄 Не получилось достать текст из файла. Если это скан, пришли страницы как фото.",
        "uk": "📄 Не вдалося дістати текст із файлу. Якщо це скан, надішли сторінки як фото.",
        "en": "📄 Couldn't extract text from the file. If it's a scan, send the pages as photos.",
    },
    "file_cut": {
        "ru": "\n\n<i>📄 Файл большой, я прочитал только начало.</i>",
        "uk": "\n\n<i>📄 Файл великий, я прочитав лише початок.</i>",
        "en": "\n\n<i>📄 The file is large, I only read the beginning.</i>",
    },
    "file_default_task": {
        "ru": "Кратко перескажи этот документ и выдели главное. Если там задания — реши их.",
        "uk": "Коротко перекажи цей документ і виділи головне. Якщо там завдання — розв'яжи їх.",
        "en": "Briefly summarize this document and highlight the key points. If it contains tasks, solve them.",
    },
    # ─── Подписка ───
    "subscribe": {
        "ru": "⭐ <b>Подписка</b>\n\n✅ До {limit} сообщений в день вместо {free}\n✅ Фото, голосовые и файлы без ограничений бесплатного тарифа\n\nОплата звёздами Telegram ⭐ — прямо в приложении. Выбери срок:",
        "uk": "⭐ <b>Підписка</b>\n\n✅ До {limit} повідомлень на день замість {free}\n✅ Фото, голосові та файли без обмежень безкоштовного тарифу\n\nОплата зірками Telegram ⭐ — прямо в застосунку. Обери термін:",
        "en": "⭐ <b>Subscription</b>\n\n✅ Up to {limit} messages per day instead of {free}\n✅ Photos, voice and files without free plan limits\n\nPay with Telegram Stars ⭐ right in the app. Choose a period:",
    },
    "sub_active_until": {
        "ru": "\n\n📅 Сейчас подписка активна до <b>{date}</b>. Новая оплата продлит её.",
        "uk": "\n\n📅 Зараз підписка активна до <b>{date}</b>. Нова оплата її продовжить.",
        "en": "\n\n📅 Your subscription is active until <b>{date}</b>. A new payment extends it.",
    },
    "plan_1_month": {"ru": "1 месяц", "uk": "1 місяць", "en": "1 month"},
    "plan_3_months": {"ru": "3 месяца", "uk": "3 місяці", "en": "3 months"},
    "plan_1_year": {"ru": "1 год", "uk": "1 рік", "en": "1 year"},
    "invoice_title": {"ru": "Подписка: {period}", "uk": "Підписка: {period}", "en": "Subscription: {period}"},
    "invoice_desc": {
        "ru": "До {limit} сообщений в день к ИИ-помощнику на {period}.",
        "uk": "До {limit} повідомлень на день до ШІ-помічника на {period}.",
        "en": "Up to {limit} messages a day to the AI assistant for {period}.",
    },
    "paid": {
        "ru": "🎉 Спасибо за оплату! Подписка активна до <b>{date}</b>.",
        "uk": "🎉 Дякуємо за оплату! Підписка активна до <b>{date}</b>.",
        "en": "🎉 Thank you! Your subscription is active until <b>{date}</b>.",
    },
    "paysupport": {
        "ru": "💬 Вопросы по оплате? Напиши администратору бота{contact}. Укажи дату оплаты — разберёмся.",
        "uk": "💬 Питання щодо оплати? Напиши адміністратору бота{contact}. Вкажи дату оплати — розберемося.",
        "en": "💬 Payment questions? Contact the bot admin{contact}. Include the payment date and we'll sort it out.",
    },
    # ─── Кнопки ───
    "btn_clear": {"ru": "🗑 Очистить историю", "uk": "🗑 Очистити історію", "en": "🗑 Clear history"},
    "btn_status": {"ru": "ℹ️ Мой статус", "uk": "ℹ️ Мій статус", "en": "ℹ️ My status"},
    "btn_subscribe": {"ru": "⭐ Подписка", "uk": "⭐ Підписка", "en": "⭐ Subscription"},
    "btn_new_chat": {"ru": "✨ Новый чат", "uk": "✨ Новий чат", "en": "✨ New chat"},
    "alert_cleared": {"ru": "🗑 История очищена!", "uk": "🗑 Історію очищено!", "en": "🗑 History cleared!"},
}

COMMANDS = {
    "ru": [("start", "🏠 Главное меню"), ("newchat", "✨ Новый чат"), ("chats", "💬 Мои чаты"),
           ("status", "📊 Мой лимит"), ("subscribe", "⭐ Подписка"), ("clear", "🗑 Очистить чат"), ("help", "❓ Помощь")],
    "uk": [("start", "🏠 Головне меню"), ("newchat", "✨ Новий чат"), ("chats", "💬 Мої чати"),
           ("status", "📊 Мій ліміт"), ("subscribe", "⭐ Підписка"), ("clear", "🗑 Очистити чат"), ("help", "❓ Допомога")],
    "en": [("start", "🏠 Main menu"), ("newchat", "✨ New chat"), ("chats", "💬 My chats"),
           ("status", "📊 My limit"), ("subscribe", "⭐ Subscription"), ("clear", "🗑 Clear chat"), ("help", "❓ Help")],
}


def t(lang: str, key: str, **kwargs) -> str:
    variants = TEXTS[key]
    text = variants.get(lang) or variants["en"]
    return text.format(**kwargs) if kwargs else text
