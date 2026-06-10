import aiosqlite
from datetime import datetime, date

DB_PATH = "bot_database.db"

async def init_db():
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

async def has_active_subscription(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT sub_expires FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if row and row[0]:
            expires = datetime.fromisoformat(row[0])
            return expires > datetime.now()
        return False

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
            "SELECT id, title FROM chats WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
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
               ORDER BY created_at DESC
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