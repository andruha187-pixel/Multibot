import aiosqlite
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица настроек копитрейдинга
        await db.execute('''
            CREATE TABLE IF NOT EXISTS copy_settings (
                user_id INTEGER PRIMARY KEY,
                mode TEXT DEFAULT 'percent',
                value REAL DEFAULT 10.0,
                slippage REAL DEFAULT 1.0,
                exit_strategy TEXT DEFAULT 'leader',
                auto_orders INTEGER DEFAULT 0,
                demo_balance REAL DEFAULT 10000.0
            )
        ''')
        # Таблица отслеживаемых кошельков
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tracked_wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                address TEXT,
                name TEXT,
                UNIQUE(user_id, address)
            )
        ''')
        # Таблица открытых демо-позиций
        await db.execute('''
            CREATE TABLE IF NOT EXISTS demo_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                wallet_address TEXT,
                market_title TEXT,
                outcome TEXT,
                amount REAL,
                entry_price REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

async def get_settings(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT mode, value, slippage, exit_strategy, auto_orders, demo_balance FROM copy_settings WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {"mode": row[0], "value": row[1], "slippage": row[2], "exit_strategy": row[3], "auto_orders": row[4], "demo_balance": row[5]}
            else:
                await db.execute("INSERT INTO copy_settings (user_id) VALUES (?)", (user_id,))
                await db.commit()
                return {"mode": "percent", "value": 10.0, "slippage": 1.0, "exit_strategy": "leader", "auto_orders": 0, "demo_balance": 10000.0}

async def update_settings(user_id: int, key: str, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE copy_settings SET {key} = ? WHERE user_id = ?", (value, user_id))
        await db.commit()
        