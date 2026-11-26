import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN
from texts import COMMANDS
from handlers import router
from database import init_db

logging.basicConfig(level=logging.INFO)

async def main():
    await init_db()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    # Меню команд на языке пользователя (по умолчанию — английский)
    for lang, commands in COMMANDS.items():
        await bot.set_my_commands(
            [BotCommand(command=c, description=d) for c, d in commands],
            language_code=None if lang == "en" else lang,
        )
    
    print("✅ Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
