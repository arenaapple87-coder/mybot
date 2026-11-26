import os
import aiosqlite
from datetime import datetime, date, timedelta

# На Railway база должна лежать на Volume, иначе она стирается при каждом обновлении.
# Укажи в Variables: DB_PATH=/data/bot_database.db
DB_PATH = os.getenv("DB_PATH", "bot_database.db")

async def init_db():
    folder = os.path.dirname(DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                created_at  TEXT DEFAULT (datetime('now')),
                sub_expires TEXT,
                messages_today  INTEGER DEFAULT 0,
                last_reset_date TEXT DEFAULT '',
                active_chat_id  INTEGER DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                title      TEXT DEFAULT 'New chat',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                chat_id    INTEGER DEFAULT 1,
                role       TEXT,
                content    TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                plan        TEXT,
                stars       INTEGER,
                charge_id   TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)
        # Новые колонки для статистики (для уже существующей базы)
        for column in ("last_active TEXT", "total_messages INTEGER DEFAULT 0"):
            try:
                await db.execute(f"ALTER TABLE users ADD COLUMN {column}")
            except aiosqlite.OperationalError:
                pass  # колонка уже есть
        await db.commit()

# ─── Пользователи ──────────────────────────────────────────────────────────

async def get_or_create_user(user_id: int, username: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            await db.execute(
                "INSERT INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username)
            )
            await db.commit()
            # Создаём первый чат
            await create_chat(user_id, "Chat 1")
            cursor = await db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
        return dict(row)

async def get_sub_expires(user_id: int):
    """Дата окончания подписки или None, если подписки нет."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT sub_expires FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if row and row[0]:
            expires = datetime.fromisoformat(row[0])
            if expires > datetime.utcnow():
                return expires
        return None

async def has_active_subscription(user_id: int) -> bool:
    return await get_sub_expires(user_id) is not None

async def extend_subscription(user_id: int, days: int, plan: str, stars: int, charge_id: str) -> datetime:
    """Продлевает подписку (от текущей даты окончания, если она ещё активна)."""
    start = await get_sub_expires(user_id) or datetime.utcnow()
    expires = start + timedelta(days=days)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET sub_expires = ? WHERE user_id = ?",
            (expires.isoformat(sep=" ", timespec="seconds"), user_id)
        )
        await db.execute(
            "INSERT INTO payments (user_id, plan, stars, charge_id) VALUES (?, ?, ?, ?)",
            (user_id, plan, stars, charge_id)
        )
        await db.commit()
    return expires

async def get_messages_today(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT messages_today, last_reset_date FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        today = str(date.today())
        if row[1] != today:
            await db.execute(
                "UPDATE users SET messages_today = 0, last_reset_date = ? WHERE user_id = ?",
                (today, user_id)
            )
            await db.commit()
            return 0
        return row[0]

async def increment_messages(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET messages_today = messages_today + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

# ─── Чаты ──────────────────────────────────────────────────────────────────

async def create_chat(user_id: int, title: str = "New chat") -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO chats (user_id, title) VALUES (?, ?)",
            (user_id, title)
        )
        chat_id = cursor.lastrowid
        await db.execute(
            "UPDATE users SET active_chat_id = ? WHERE user_id = ?",
            (chat_id, user_id)
        )
        await db.commit()
        return chat_id

async def get_active_chat_id(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT active_chat_id FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 1

async def set_active_chat(user_id: int, chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET active_chat_id = ? WHERE user_id = ?",
            (chat_id, user_id)
        )
        await db.commit()

async def get_user_chats(user_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, title FROM chats WHERE user_id = ? ORDER BY id DESC LIMIT 10",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [{"id": r[0], "title": r[1]} for r in rows]

async def update_chat_title(chat_id: int, title: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE chats SET title = ? WHERE id = ?",
            (title, chat_id)
        )
        await db.commit()

# ─── История сообщений ─────────────────────────────────────────────────────

async def save_message(user_id: int, role: str, content: str):
    chat_id = await get_active_chat_id(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO history (user_id, chat_id, role, content) VALUES (?, ?, ?, ?)",
            (user_id, chat_id, role, content)
        )
        await db.commit()

async def get_history(user_id: int, limit: int = 20) -> list:
    chat_id = await get_active_chat_id(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT role, content FROM history
               WHERE user_id = ? AND chat_id = ?
               ORDER BY id DESC
               LIMIT ?""",
            (user_id, chat_id, limit)
        )
        rows = await cursor.fetchall()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

async def clear_history(user_id: int):
    chat_id = await get_active_chat_id(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM history WHERE user_id = ? AND chat_id = ?",
            (user_id, chat_id)
        )
        await db.commit()

# ─── Статистика ────────────────────────────────────────────────────────────

async def touch_user(user_id: int):
    """Отмечает, что пользователь получил ответ от ИИ (для статистики)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE users SET last_active = datetime('now'),
                                total_messages = COALESCE(total_messages, 0) + 1
               WHERE user_id = ?""",
            (user_id,)
        )
        await db.commit()

async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async def one(sql):
            cursor = await db.execute(sql)
            row = await cursor.fetchone()
            return row[0] or 0

        return {
            "users_total":   await one("SELECT COUNT(*) FROM users"),
            "users_new_today": await one("SELECT COUNT(*) FROM users WHERE date(created_at) = date('now')"),
            "users_new_week":  await one("SELECT COUNT(*) FROM users WHERE created_at >= datetime('now', '-7 days')"),
            "active_today":  await one("SELECT COUNT(*) FROM users WHERE date(last_active) = date('now')"),
            "active_week":   await one("SELECT COUNT(*) FROM users WHERE last_active >= datetime('now', '-7 days')"),
            "active_month":  await one("SELECT COUNT(*) FROM users WHERE last_active >= datetime('now', '-30 days')"),
            "msgs_today":    await one("SELECT COUNT(*) FROM history WHERE role = 'user' AND date(created_at) = date('now')"),
            "msgs_total":    await one("SELECT SUM(total_messages) FROM users"),
            "subscribers":   await one("SELECT COUNT(*) FROM users WHERE sub_expires > datetime('now')"),
            "stars_total":   await one("SELECT SUM(stars) FROM payments"),
            "stars_month":   await one("SELECT SUM(stars) FROM payments WHERE created_at >= datetime('now', '-30 days')"),
        }
