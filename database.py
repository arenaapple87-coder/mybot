import aiosqlite
from datetime import datetime, date

DB_PATH = "bot_database.db"

async def init_db():
    """Создаёт таблицы при первом запуске."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                created_at  TEXT DEFAULT (datetime('now')),
                
                -- Подписка
                sub_expires TEXT,   -- дата окончания подписки (NULL = нет)
                
                -- Лимиты для бесплатных
                messages_today  INTEGER DEFAULT 0,
                last_reset_date TEXT DEFAULT ''
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                role       TEXT,   -- 'user' или 'assistant'
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

async def add_subscription(user_id: int, days: int):
    """Добавляет или продлевает подписку."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT sub_expires FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        
        now = datetime.now()
        if row and row[0]:
            current = datetime.fromisoformat(row[0])
            base = current if current > now else now
        else:
            base = now
        
        from datetime import timedelta
        new_expires = base + timedelta(days=days)
        
        await db.execute(
            "UPDATE users SET sub_expires = ? WHERE user_id = ?",
            (new_expires.isoformat(), user_id)
        )
        await db.commit()
        return new_expires

async def get_messages_today(user_id: int) -> int:
    """Возвращает кол-во сообщений за сегодня, сбрасывает счётчик если новый день."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT messages_today, last_reset_date FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        today = str(date.today())
        
        if row[1] != today:
            # Новый день — сброс счётчика
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

# ─── История сообщений ─────────────────────────────────────────────────────

async def save_message(user_id: int, role: str, content: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content)
        )
        await db.commit()

async def get_history(user_id: int, limit: int = 20) -> list:
    """Возвращает последние N сообщений для передачи в Claude."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT role, content FROM history
               WHERE user_id = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        # Разворачиваем — старые сообщения первыми
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

async def clear_history(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
        await db.commit()