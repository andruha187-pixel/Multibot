import aiohttp
import logging

logger = logging.getLogger(__name__)

# Меняем эндпоинт на актуальный публичный API лидерборда Polymarket
POLYMARKET_LEADERBOARD_URL = "https://gamma-api.polymarket.com/leaderboard"

async def fetch_real_wallets(category: str, strategy_type: str):
    """
    Запрашивает реальные данные с официального Gamma API Polymarket.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Origin": "https://polymarket.com",
        "Referer": "https://polymarket.com/"
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=7.0)) as session:
            # Настраиваем параметры под тип лидерборда (pnl или volume)
            # По умолчанию берем за все время (all), либо можно поставить 'monthly'/'weekly'
            params = {
                "window": "all",
                "limit": "20"
            }
            
            logger.info(f"Отправка запроса к Gamma API: {POLYMARKET_LEADERBOARD_URL} с параметрами {params}")
            
            async with session.get(POLYMARKET_LEADERBOARD_URL, params=params) as response:
                logger.info(f"Ответ от Polymarket API получен. Статус: {response.status}")
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Polymarket API вернул ошибку {response.status}: {error_text[:200]}")
                    return []
                
                data = await response.json()
                
                # В Gamma API структура может возвращаться списком или объектом со списком внутри
                raw_users = data if isinstance(data, list) else data.get("users", [])
                
                if not raw_users:
                    logger.warning("Polymarket API вернул пустой список лидеров.")
                    return []
                
                wallets = []
                for i, user in enumerate(raw_users):
                    # Извлекаем адрес (в Gamma API он обычно в поле 'proxyWallet' или 'id')
                    address = user.get("proxyWallet") or user.get("id") or user.get("address")
                    
                    if not address or not str(address).startswith("0x"):
                        continue
                        
                    # Извлекаем метрики прибыли и объема
                    pnl = float(user.get("pnl", 0)) or float(user.get("profit", 0))
                    volume = float(user.get("volume", 0))
                    
                    # Имя пользователя или красивый псевдоним
                    name = user.get("displayName") or user.get("username") or f"Trader_{i+1}"
                    
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
                            "metric": f"Объем: ${volume:,.0f} | Ранг: #{i+1}"
                        })
                    elif strategy_type == "flip":
                        wallets.append({
                            "name": name,
                            "address": address,
                            "price": f"${0.50:.2f}",
                            "pot": f"{(pnl/10000 if pnl > 0 else 1.5):.1f}x"
                        })
                    elif strategy_type == "auto":
                        wallets.append({
                            "name": name,
                            "address": address,
                            "metric": f"Суммарный PnL: +${pnl:,.0f}"
                        })

                logger.info(f"Успешно обработано {len(wallets)} реальных кошельков.")
                return wallets[:15]
                
    except Exception as e:
        logger.error(f"Критическое исключение в парсере: {e}", exc_info=True)
        return []
                
