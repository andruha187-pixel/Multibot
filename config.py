import os
from dotenv import load_dotenv

load_dotenv()

# Все чувствительные данные берутся строго из переменных окружения Render
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
DB_PATH = os.getenv("DB_PATH", "bot_data.db")

if not BOT_TOKEN:
    print("ВНИМАНИЕ: Переменная окружения BOT_TOKEN не задана!")
    