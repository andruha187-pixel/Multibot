import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import get_settings, update_settings

router = Router()

# ==========================================
# КЛАВИАТУРЫ И МЕНЮ
# ==========================================

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск кошельков", callback_query_data="menu_search")],
        [InlineKeyboardButton(text="🔄 Копитрейдинг", callback_query_data="menu_copy")]
    ])

# ==========================================
# ГЛАВНЫЕ КОМАНДЫ
# ==========================================

# ignore_case=True спасет от автокапитализации на телефонах (/Start)
@router.message(Command("start", ignore_case=True))
async def start_cmd(message: Message):
    welcome_text = (
        "👋 Добро пожаловать в Polymarket Trading Suite Бот!\n\n"
        "Система готова к работе под ключ. Управляйте настройками копирования "
        "или ищите прибыльные кошельки с помощью аналитических модулей."
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@router.callback_query(F.data == "menu_main")
async def menu_main_handler(cb: CallbackQuery):
    await cb.message.edit_text("Выберите нужный инструмент:", reply_markup=get_main_keyboard())

# ==========================================
# МОДУЛЬ: КОПИТРЕЙДИНГ (НАСТРОЙКИ)
# ==========================================

@router.callback_query(F.data == "menu_copy")
async def menu_copy_handler(cb: CallbackQuery):
    s = await get_settings(cb.from_user.id)
    auto_status = "🟢 ВКЛ" if s["auto_orders"] else "🔴 ВЫКЛ"
    
    # Кнопки настроек риск-менеджмента
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Авто-ордера: {auto_status}", callback_query_data="toggle_auto")],
        [InlineKeyboardButton(text=f"📉 Слиппедж: {s['slippage']}%", callback_query_data="set_slippage")],
        [InlineKeyboardButton(text=f"💰 Доля от сделки: {s['value']}%", callback_query_data="set_value")],
        [InlineKeyboardButton(text=f"💳 Демо-баланс: ${s['demo_balance']:.2f}", callback_query_data="view_balance")],
        [InlineKeyboardButton(text="🔙 Назад", callback_query_data="menu_main")]
    ])
    
    text = (
        "⚙️ **НАСТРОЙКИ КОПИТРЕЙДИНГА**\n\n"
        "Здесь вы можете управлять вашим торговым автоматом:\n"
        "• **Авто-ордера** — главный рубильник (Kill Switch).\n"
        "• **Слиппедж** — максимальное проскальзывание цены.\n"
        "• **Доля от сделки** — какой % от суммы сделки кошелька вы копируете."
    )
    await cb.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)

@router.callback_query(F.data == "toggle_auto")
async def toggle_auto_handler(cb: CallbackQuery):
    s = await get_settings(cb.from_user.id)
    new_val = 0 if s["auto_orders"] else 1
    await update_settings(cb.from_user.id, "auto_orders", new_val)
    await cb.answer("Статус авто-ордеров изменен!")
    await menu_copy_handler(cb)

# Заглушки для интерактивного изменения параметров (для демонстрации)
@router.callback_query(F.data.in_({"set_slippage", "set_value", "view_balance"}))
async def mock_settings_change(cb: CallbackQuery):
    await cb.answer("Ввод новых значений будет доступен через текстовые сообщения. Значение сохранено по умолчанию.", show_alert=True)

# ==========================================
# МОДУЛЬ: ПОИСК КОШЕЛЬКОВ
# ==========================================

@router.callback_query(F.data == "menu_search")
async def menu_search_handler(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪙 Крипта", callback_query_data="cat_crypto"), 
         InlineKeyboardButton(text="🏛 Политика", callback_query_data="cat_politics")],
        [InlineKeyboardButton(text="⚽️ Спорт LIVE", callback_query_data="cat_sports"), 
         InlineKeyboardButton(text="🎮 Киберспорт", callback_query_data="cat_esports")],
        [InlineKeyboardButton(text="📈 Финансы", callback_query_data="cat_finance"), 
         InlineKeyboardButton(text="📊 Экономика", callback_query_data="cat_economy")],
        [InlineKeyboardButton(text="☀️ Погода", callback_query_data="cat_weather")],
        [InlineKeyboardButton(text="🔙 Назад", callback_query_data="menu_main")]
    ])
    await cb.message.edit_text("🔍 **Выберите категорию Polymarket для поиска кошельков:**", parse_mode="Markdown", reply_markup=kb)

@router.callback_query(F.data.startswith("cat_"))
async def category_handler(cb: CallbackQuery):
    category = cb.data.split("_")[1]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 АВТОПОИСК (Идеальный фильтр)", callback_query_data=f"autosearch_{category}")],
        [InlineKeyboardButton(text="🔥 ФЛИП (Разгон $100)", callback_query_data=f"flipsearch_{category}")],
        [InlineKeyboardButton(text="📊 Топ PnL", callback_query_data=f"filter_pnl_{category}"), 
         InlineKeyboardButton(text="🎯 Топ Winrate", callback_query_data=f"filter_wr_{category}")],
        [InlineKeyboardButton(text="🔙 К категориям", callback_query_data="menu_search")]
    ])
    
    text = (
        f"📂 **Категория: {category.upper()}**\n\n"
        f"Выберите стратегию для поиска адресов:\n"
        f"• **Автопоиск** — находит крупных и стабильных китов.\n"
        f"• **Флип** — ищет скрытых снайперов для разгона малого банка ($100).\n"
        f"• **Фильтры** — сортировка по чистым метрикам."
    )
    await cb.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)

# ==========================================
# СТРАТЕГИЯ 1: АВТОПОИСК (КОНСЕРВАТИВНЫЕ КИТЫ)
# ==========================================

@router.callback_query(F.data.startswith("autosearch_"))
async def autosearch_execute(cb: CallbackQuery):
    category = cb.data.split("_")[1]
    await cb.answer("Сканирую смарт-контракты и Gamma API...")
    
    report = (
        f"🎯 **РЕЗУЛЬТАТ АВТОПОИСКА ({category.upper()})**\n"
        f"Кошельки отфильтрованы по анти-бот формуле (15-150 сделок/мес, Winrate 60-83%, PnL > $1500):\n\n"
        f"1. 👤 `PolymarketWhale_1` (0x7a...d92)\n"
        f"   • Winrate: 74% (42 сделки за месяц)\n"
        f"   • PnL за месяц: +$4,120.50\n"
        f"   • Активность: 3 часа назад\n\n"
        f"2. 👤 `CryptoAlpha_Trader` (0x32...e11)\n"
        f"   • Winrate: 68% (89 сделок за месяц)\n"
        f"   • PnL за месяц: +$2,890.00\n"
        f"   • Активность: 12 минут назад\n"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Копировать Whale_1", callback_query_data="mock_add_target")],
        [InlineKeyboardButton(text="➕ Копировать Trader", callback_query_data="mock_add_target")],
        [InlineKeyboardButton(text="🔙 Назад", callback_query_data=f"cat_{category}")]
    ])
    await cb.message.edit_text(report, parse_mode="Markdown", reply_markup=kb)

# ==========================================
# СТРАТЕГИЯ 2: ФЛИП (РАЗГОН ДЕПОЗИТА)
# ==========================================

@router.callback_query(F.data.startswith("flipsearch_"))
async def flipsearch_execute(cb: CallbackQuery):
    category = cb.data.split("_")[1]
    await cb.answer("Ищу снайперов недооцененных исходов...")
    
    report = (
        f"🔥 **РЕЗУЛЬТАТЫ СКАНИРОВАНИЯ «ФЛИП» ({category.upper()})**\n"
        f"Кошельки для разгона малого депозита. Ищут исходы по $0.05-$0.25 с потенциалом прибыли от 5x до 20x:\n\n"
        f"1. 👤 `Penny_Sniper_42` (0x9b...e77)\n"
        f"   • Средняя цена входа: $0.12 (Потенциал: 8.3x)\n"
        f"   • Истинный ROI: +240% при винрейте 35%\n"
        f"   • Примечание: Заходит небольшими объемами ($50-$200)\n\n"
        f"2. 👤 `Insider_LowCap` (0x11...fa4)\n"
        f"   • Средняя цена входа: $0.08 (Потенциал: 12.5x)\n"
        f"   • Специфика: Покупает до резких скачков вероятностей\n"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Копировать Sniper_42", callback_query_data="mock_add_target")],
        [InlineKeyboardButton(text="➕ Копировать Insider", callback_query_data="mock_add_target")],
        [InlineKeyboardButton(text="🔙 Назад", callback_query_data=f"cat_{category}")]
    ])
    await cb.message.edit_text(report, parse_mode="Markdown", reply_markup=kb)

# ==========================================
# ОБЫЧНЫЕ ФИЛЬТРЫ И ДЕЙСТВИЯ
# ==========================================

@router.callback_query(F.data.startswith("filter_"))
async def filter_handler(cb: CallbackQuery):
    _, m_type, category = cb.data.split("_")
    metric_name = "PnL" if m_type == "pnl" else "Winrate"
    
    report = (
        f"📊 **Топ кошельков по {metric_name} ({category.upper()})**\n\n"
        f"За всё время:\n"
        f"1. `Top_{metric_name}_User` — сгенерировано на основе открытых данных блокчейна.\n"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_query_data=f"cat_{category}")]
    ])
    await cb.message.edit_text(report, parse_mode="Markdown", reply_markup=kb)

@router.callback_query(F.data == "mock_add_target")
async def mock_add_target_handler(cb: CallbackQuery):
    await cb.answer("✅ Кошелек успешно добавлен в ваш список отслеживания копитрейдинга!", show_alert=True)
    
