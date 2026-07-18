import random
from database import get_settings, update_settings

async def process_signal(user_id: int, wallet: str, market: str, outcome: str, whale_amount: float, whale_price: float):
    settings = await get_settings(user_id)
    
    if not settings["auto_orders"]:
        return f"⚠️ [Наблюдение] Кошелек {wallet} совершил сделку на рынке '{market}' ({outcome}) на ${whale_amount:.2f}. Авто-ордера выключены."

    # Моделируем текущую рыночную цену со случайным сдвигом для проверки слиппеджа
    price_deviation = random.uniform(-0.02, 0.02)
    current_price = whale_price + price_deviation
    
    # Расчет проскальзывания в %
    slippage_pc = abs(current_price - whale_price) / whale_price * 100
    if slippage_pc > settings["slippage"]:
        return f"❌ Сделка отклонена! Превышен лимит проскальзывания ({slippage_pc:.2f}% > {settings['slippage']}%) на рынке '{market}'."

    # Расчет суммы ордера (процент от сделки кита)
    my_amount = whale_amount * (settings["value"] / 100.0)
    
    if settings["demo_balance"] < my_amount:
        return f"❌ Недостаточно средств на Демо-счете (${settings['demo_balance']:.2f}) для копирования сделки на ${my_amount:.2f}."

    new_balance = settings["demo_balance"] - my_amount
    await update_settings(user_id, "demo_balance", new_balance)
    
    return f"🟢 [ДЕМО-КОПИЯ] Успешно куплено {outcome} на рынке '{market}'!\n💰 Сумма сделки: ${my_amount:.2f} (Цена: ${current_price:.2f})\n📉 Слиппедж: {slippage_pc:.2f}%\n💳 Демо-баланс: ${new_balance:.2f}"
    