import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from aiohttp import web  # Добавили встроенную библиотеку aiohttp

from bot_ui import router
from database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Хэндлер для проверки от Render (Health Check)
async def handle_health(request):
    return web.Response(text="Бот работает!")

async def main():
    load_dotenv()
    
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN не найден в настройках!")
        return

    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    logger.info("Инициализация базы данных...")
    await init_db()
    
    # --- Запуск веб-сервера-"заглушки" для Render ---
    app = web.Application()
    app.router.add_get('/', handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render автоматически передает нужный порт в переменную PORT
    port = int(os.getenv("PORT", 10000)) 
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Веб-заглушка запущена на порту {port}")
    # -----------------------------------------------

    logger.info("Бот запущен и готов к работе.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
