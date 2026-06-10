import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN
from handlers import router
from database import init_db

logging.basicConfig(level=logging.INFO)

async def main():
    await init_db()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 Main menu"),
        BotCommand(command="newchat", description="✨ New chat"),
        BotCommand(command="chats", description="💬 My chats"),
        BotCommand(command="status", description="📊 Message limit"),
        BotCommand(command="clear", description="🗑 Clear current chat"),
        BotCommand(command="help", description="❓ Help"),
    ])
    
    print("✅ Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
