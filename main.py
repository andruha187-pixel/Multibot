import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Импортируем интерфейс и базу данных из твоих файлов
from bot_ui import router
from database import init_db

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Загружаем переменные из .env (или из настроек Render)
    load_dotenv()
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("Критическая ошибка: Переменная BOT_TOKEN не задана в настройках Render!")
        
    # Инициализируем бота и диспетчер
    bot = Bot(token=bot_token)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Подключаем роутер из bot_ui.py
    dp.include_router(router)
    
    # Инициализируем базу данных (создаем таблицы, если их нет)
    await init_db()
    
    logger.info("Бот успешно инициализирован и запускает пуллинг...")
    
    # Запуск бота (удаляем вебхуки, если были, и включаем long polling)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
