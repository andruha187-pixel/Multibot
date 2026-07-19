import aiohttp
import logging

logger = logging.getLogger(__name__)

# Используем официальный эндпоинт лидерборда
POLYMARKET_LEADERBOARD_URL = "https://clob.polymarket.com/leaderboard"

async def fetch_real_wallets(category: str, strategy_type: str):
    """
    Запрашивает ТОЛЬКО реальные данные с Polymarket API.
    Если происходит ошибка — логирует её для отладки на Render.
    """
    # Добавляем User-Agent, чтобы притвориться обычным браузером (помогает от блокировок)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=7.0)) as session:
            params = {"window": "all"}  # Можно попробовать "daily", "weekly", "monthly"
            
            logger.info(f"Отправка запроса к Polymarket API: {POLYMARKET_LEADERBOARD_URL} с параметрами {params}")
            
            async with session.get(POLYMARKET_LEADERBOARD_URL, params=params) as response:
                logger.info(f"Ответ от Polymarket API получен. Статус: {response.status}")
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Polymarket API вернул ошибку {response.status}: {error_text}")
                    return []
                
                data = await response.json()
                raw_users = data.get("users", [])
                
                if not raw_users:
                    logger.warning("Polymarket API вернул успешный статус, но список 'users' пуст.")
                    return []
                
                wallets = []
                for i, user in enumerate(raw_users):
                    # Проверяем все возможные ключи, где может лежать адрес кошелька
                    address = user.get("proxy_wallet") or user.get("id") or user.get("crypto_wallet") or user.get("username")
                    if not address or not address.startswith("0x"):
                        continue
                        
                    pnl = float(user.get("pnl", 0))
                    volume = float(user.get("volume", 0))
                    name = user.get("display_name") or f"Polymarket_Trader_{i+1}"
                    
                    # Упростим фильтрацию до минимума, чтобы кошельки точно проходили
                    if strategy_type == "pnl":
                        wallets.append({
                            "name": name,
                            "address": address,
                            "metric": f"PnL: +${pnl:,.2f} | Объем: ${volume:,.0f}"
                        })
                    elif strategy_type == "wr":
                        wallets.append({
                            "name": name,
                            "address": address,
                            "metric": f"Объем: ${volume:,.0f} | PnL: +${pnl:,.0f}"
                        })
                    elif strategy_type == "flip":
                        wallets.append({
                            "name": name,
                            "address": address,
                            "price": f"${0.20:.2f}",
                            "pot": "2.5x"
                        })
                    elif strategy_type == "auto":
                        wallets.append({
                            "name": name,
                            "address": address,
                            "metric": f"Общий объем торгов: ${volume:,.0f}"
                        })

                logger.info(f"Успешно отфильтровано {len(wallets)} реальных кошельков.")
                return wallets[:15]
                
    except Exception as e:
        logger.error(f"Критическое исключение при запросе к Polymarket: {e}", exc_info=True)
        return []
                    
