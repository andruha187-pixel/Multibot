import aiosqlite
import os

DB_PATH = "bot_database.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица основных настроек пользователя
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER PRIMARY KEY,
                auto_orders INTEGER DEFAULT 0,
                slippage REAL DEFAULT 1.0,
                value REAL DEFAULT 10.0,
                demo_balance REAL DEFAULT 10000.0
            )
        """)
        # Новая таблица для хранения добавленных адресов на копирование
        await db.execute("""
            CREATE TABLE IF NOT EXISTS copytrading_wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                address TEXT,
                UNIQUE(user_id, address)
            )
        """)
        await db.commit()

async def get_settings(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT auto_orders, slippage, value, demo_balance FROM settings WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "auto_orders": row[0],
                    "slippage": row[1],
                    "value": row[2],
                    "demo_balance": row[3]
                }
            else:
                # Если пользователя нет в базе, создаем дефолтные настройки
                await db.execute("INSERT INTO settings (user_id) VALUES (?)", (user_id,))
                await db.commit()
                return {"auto_orders": 0, "slippage": 1.0, "value": 10.0, "demo_balance": 10000.0}

async def update_settings(user_id: int, field: str, value):
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем существование записи
        await get_settings(user_id)
        await db.execute(f"UPDATE settings SET {field} = ? WHERE user_id = ?", (value, user_id))
        await db.commit()

# --- НОВЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С КОПИТРЕЙДИНГОМ ---

async def add_to_copytrading(user_id: int, name: str, address: str):
    """Добавляет кошелек для отслеживания в базу данных"""
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT OR IGNORE INTO copytrading_wallets (user_id, name, address) VALUES (?, ?, ?)",
                (user_id, name, address)
            )
            await db.commit()
        except Exception as e:
            print(f"Ошибка при добавлении адреса: {e}")

async def get_active_copy_wallets(user_id: int):
    """Возвращает список всех кошельков, добавленных пользователем"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT name, address FROM copytrading_wallets WHERE user_id = ?", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [{"name": row[0], "address": row[1]} for row in rows]
            
