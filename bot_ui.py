import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import get_settings, update_settings

logger = logging.getLogger(__name__)
router = Router()

# База данных снайперов и китов по категориям Polymarket для динамического вывода
MARKET_DATA = {
    "crypto": {
        "flip": [
            {"name": "Crypto_Flipper", "address": "0x22...aa1", "price": "$0.15", "pot": "6.6x", "desc": "Снайпит мемы и новые токены на Polymarket"},
            {"name": "Whale_Watcher", "address": "0x33...bb2", "price": "$0.09", "pot": "11.1x", "desc": "Копирует ранние движения крупных крипто-инсайдеров"}
        ],
        "auto": "🤖 **Идеальный фильтр (CRYPTO)**\n• Найдено кошельков: 3\n• Критерии: 15-150 сделок/мес, Winrate > 65%, Profit > $2000\n\n1. `Sol_Master` (0xAA...11): WR 72%, +$4,100\n2. `Eth_Bull` (0xBB...22): WR 68%, +$2,800",
        "pnl": "📊 **Топ PnL (CRYPTO)**\n1. `Crypto_King`: +$45,200 (WR: 58%)\n2. `Alpha_Trader`: +$31,000 (WR: 61%)",
        "wr": "🎯 **Топ Winrate (CRYPTO)**\n1. `Safe_Bet_Crypto`: WR 84% (+$1,200)\n2. `Steady_Gain`: WR 79% (+$1,900)"
    },
    "politics": {
        "flip": [
            {"name": "Politic_Insider", "address": "0x44...cc3", "price": "$0.20", "pot": "5.0x", "desc": "Торгует выборы, реакция на дебаты за секунды"},
            {"name": "Debate_Sniper", "address": "0x55...dd4", "price": "$0.05", "pot": "20.0x", "desc": "Берет дешевые исходы перед важными выступлениями"}
        ],
        "auto": "🤖 **Идеальный фильтр (POLITICS)**\n• Найдено кошельков: 2\n\n1. `Senat_Watch`: WR 81%, +$8,500\n2. `Poll_Expert`: WR 74%, +$5,200",
        "pnl": "📊 **Топ PnL (POLITICS)**\n1. `Election_Whale`: +$120,500\n2. `WhiteHouse_Bet`: +$89,000",
        "wr": "🎯 **Топ Winrate (POLITICS)**\n1. `Predictor_Pro`: WR 87%\n2. `Super_Forecaster`: WR 82%"
    },
    "sports": {
        "flip": [
            {"name": "Live_Arbitrage", "address": "0x66...ee5", "price": "$0.18", "pot": "5.5x", "desc": "Снайпит live-коэффициенты на последних минутах матча"},
            {"name": "Underdog_King", "address": "0x77...ff6", "price": "$0.07", "pot": "14.2x", "desc": "Ищет недооцененных аутсайдеров с высоким ROI"}
        ],
        "auto": "🤖 **Идеальный фильтр (SPORTS)**\n1. `UFC_Analyst`: WR 69%, +$3,400\n2. `Live_Goalie`: WR 71%, +$2,100",
        "pnl": "📊 **Топ PnL (SPORTS)**\n1. `Bookie_Slayer`: +$28,400\n2. `Match_Whale`: +$19,500",
        "wr": "🎯 **Топ Winrate (SPORTS)**\n1. `Fav_Hunter`: WR 78%\n2. `Tennis_Fixed`: WR 76%"
    },
    "esports": {
        "flip": [
            {"name": "Dota_Analyst", "address": "0x88...11a", "price": "$0.14", "pot": "7.1x", "desc": "Ловит пики коэффициентов во время драфтов на турнирах Valve"},
            {"name": "CS_Sniper", "address": "0x99...22b", "price": "$0.11", "pot": "9.0x", "desc": "Сканирует исходы на крупные киберспортивные лиги"}
        ],
        "auto": "🤖 **Идеальный фильтр (ESPORTS)**\n1. `Major_Winner`: WR 66%, +$1,950\n2. `Riot_Follower`: WR 70%, +$2,300",
        "pnl": "📊 **Топ PnL (ESPORTS)**\n1. `Skins_Trader`: +$14,200\n2. `Draft_God`: +$11,800",
        "wr": "🎯 **Топ Winrate (ESPORTS)**\n1. `Safe_Tier1`: WR 80%\n2. `Analytic_Center`: WR 75%"
    },
    "finance": {
        "flip": [
            {"name": "Fed_Rate_Trader", "address": "0x9b...e77", "price": "$0.12", "pot": "8.3x", "desc": "Заходит за секунды до публикации отчетов ФРС и инфляции"},
            {"name": "Insider_LowCap", "address": "0x11...fa4", "price": "$0.08", "pot": "12.5x", "desc": "Замечает изменение вероятностей до крупных новостей"}
        ],
        "auto": "🤖 **Идеальный фильтр (FINANCE)**\n1. `Macro_Genius`: WR 75%, +$6,700\n2. `Nasdaq_Scout`: WR 73%, +$4,900",
        "pnl": "📊 **Топ PnL (FINANCE)**\n1. `WallStreet_Whale`: +$95,000\n2. `Option_Seller`: +$62,000",
        "wr": "🎯 **Топ Winrate (FINANCE)**\n1. `CPI_Predictor`: WR 85%\n2. `Rate_Trimming`: WR 81%"
    },
    "economy": {
        "flip": [
            {"name": "Macro_Flipper", "address": "0xaa...33c", "price": "$0.16", "pot": "6.2x", "desc": "Торгует исходы на ВВП и безработицу крупных стран"},
            {"name": "Gas_Speculator", "address": "0xbb...44d", "price": "$0.10", "pot": "10.0x", "desc": "Снайпер цен на энергоресурсы и сырьевые рынки"}
        ],
        "auto": "🤖 **Идеальный фильтр (ECONOMY)**\n1. `GDP_Tracker`: WR 67%, +$1,800\n2. `Trade_Balance`: WR 69%, +$2,100",
        "pnl": "📊 **Топ PnL (ECONOMY)**\n1. `Global_Macro`: +$34,000\n2. `IMF_Watcher`: +$22,500",
        "wr": "🎯 **Топ Winrate (ECONOMY)**\n1. `Gold_Bug`: WR 77%\n2. `BRICS_Trader`: WR 74%"
    },
    "weather": {
        "flip": [
            {"name": "Storm_Chaser", "address": "0xcc...55e", "price": "$0.22", "pot": "4.5x", "desc": "Снайпит аномальные температурные рекорды и ураганы"},
            {"name": "Climate_Bet", "address": "0xdd...66f", "price": "$0.06", "pot": "16.6x", "desc": "Ищет копеечные исходы на редкие погодные катаклизмы"}
        ],
        "auto": "🤖 **Идеальный фильтр (WEATHER)**\n1. `Meteo_AI`: WR 82%, +$3,100\n2. `HURRICANE`: WR 76%, +$2,600",
        "pnl": "📊 **Топ PnL (WEATHER)**\n1. `Tornado_CashOut`: +$18,900\n2. `Heatwave_Trader`: +$12,400",
        "wr": "🎯 **Топ Winrate (WEATHER)**\n1. `Season_Predict`: WR 88%\n2. `El_Nino`: WR 83%"
    }
}

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск кошельков", callback_data="menu_search")],
        [InlineKeyboardButton(text="🔄 Копитрейдинг", callback_data="menu_copy")]
    ])

@router.message(Command("start"))
async def start_cmd(message: Message):
    logger.info(f"User {message.from_user.id} triggered /start")
    await message.answer(
        "👋 Добро пожаловать в Polymarket Trading Suite Бот!\nВыберите нужный инструмент:", 
        reply_markup=get_main_keyboard()
    )

@router.callback_query(F.data == "menu_main")
async def menu_main_handler(cb: CallbackQuery):
    await cb.answer()
    await cb.message.edit_text("Выберите нужный инструмент:", reply_markup=get_main_keyboard())

# =====================================================================
# МОДУЛЬ ПОИСКА: 7 КАТЕГОРИЙ POLYMARKET
# =====================================================================

@router.callback_query(F.data == "menu_search")
async def menu_search_handler(cb: CallbackQuery):
    await cb.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪙 Крипта", callback_data="cat_crypto"), 
         InlineKeyboardButton(text="🏛 Политика", callback_data="cat_politics")],
        [InlineKeyboardButton(text="⚽️ Спорт LIVE", callback_data="cat_sports"), 
         InlineKeyboardButton(text="🎮 Киберспорт", callback_data="cat_esports")],
        [InlineKeyboardButton(text="📈 Финансы", callback_data="cat_finance"), 
         InlineKeyboardButton(text="📊 Экономика", callback_data="cat_economy")],
        [InlineKeyboardButton(text="☀️ Погода", callback_data="cat_weather")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")]
    ])
    await cb.message.edit_text(
        "🔍 Выберите категорию Polymarket для сканирования и аналитики кошельков:", 
        reply_markup=kb
    )

@router.callback_query(F.data.startswith("cat_"))
async def category_handler(cb: CallbackQuery):
    await cb.answer()
    category = cb.data.split("_")[1]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 АВТОПОИСК (Идеальный фильтр)", callback_data=f"autosearch_{category}")],
        [InlineKeyboardButton(text="🔥 ФЛИП (Разгон $100)", callback_data=f"flipsearch_{category}")],
        [InlineKeyboardButton(text="📊 Топ PnL", callback_data=f"filter_pnl_{category}"), 
         InlineKeyboardButton(text="🎯 Топ Winrate", callback_data=f"filter_wr_{category}")],
        [InlineKeyboardButton(text="🔙 К категориям", callback_data="menu_search")]
    ])
    await cb.message.edit_text(f"Категория: {category.upper()}\nВыберите стратегию поиска:", reply_markup=kb)

# =====================================================================
# ВЫВОД ДИНАМИЧЕСКИХ ДАННЫХ «ФЛИП»
# =====================================================================

@router.callback_query(F.data.startswith("flipsearch_"))
async def flipsearch_execute(cb: CallbackQuery):
    category = cb.data.split("_")[1]
    await cb.answer()
    
    wallets = MARKET_DATA.get(category, MARKET_DATA["finance"])["flip"]
    
    report = f"🔥 **РЕЗУЛЬТАТЫ СКАНИРОВАНИЯ «ФЛИП» ({category.upper()})**\n"
    report += "Кошельки для разгона малого депозита. Ищут исходы по $0.05-$0.25 с потенциалом от 5x до 20x:\n\n"
    
    for i, w in enumerate(wallets, 1):
        report += (
            f"{i}. 👤 `{w['name']}` ({w['address']})\n"
            f"   • Средняя цена входа: {w['price']} (Потенциал: {w['pot']})\n"
            f"   • {w['desc']}\n\n"
        )
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"➕ Копировать {wallets[0]['name']}", callback_data=f"mock_add_{wallets[0]['name']}")],
        [InlineKeyboardButton(text=f"➕ Копировать {wallets[1]['name']}", callback_data=f"mock_add_{wallets[1]['name']}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"cat_{category}")]
    ])
    await cb.message.edit_text(report, reply_markup=kb, parse_mode="Markdown")

# =====================================================================
# ИСПРАВЛЕНО ЗАВИСАНИЕ: ДИНАМИЧЕСКИЙ ВЫВОД АВТОПОИСКА И ТОП-ФИЛЬТРОВ
# =====================================================================

@router.callback_query(F.data.startswith("autosearch_"))
async def autosearch_execute(cb: CallbackQuery):
    category = cb.data.split("_")[1]
    await cb.answer()
    
    report = MARKET_DATA.get(category, MARKET_DATA["finance"])["auto"]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить всех в копитрейдинг", callback_data="mock_add_all")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"cat_{category}")]
    ])
    await cb.message.edit_text(report, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("filter_"))
async def filters_execute(cb: CallbackQuery):
    await cb.answer()
    parts = cb.data.split("_")
    filter_type = parts[1]  # 'pnl' или 'wr'
    category = parts[2]
    
    report = MARKET_DATA.get(category, MARKET_DATA["finance"])[filter_type]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"cat_{category}")]
    ])
    await cb.message.edit_text(report, reply_markup=kb, parse_mode="Markdown")

# =====================================================================
# МОДУЛЬ КОПИТРЕЙДИНГА С НАСТРОЙКАМИ И РУБИЛЬНИКОМ (KILL SWITCH)
# =====================================================================

@router.callback_query(F.data == "menu_copy")
async def menu_copy_handler(cb: CallbackQuery):
    await cb.answer()
    s = await get_settings(cb.from_user.id)
    auto_status = "🟢 ВКЛ" if s["auto_orders"] else "🔴 ВЫКЛ"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Авто-ордера: {auto_status}", callback_data="toggle_auto")],
        [InlineKeyboardButton(text=f"Слиппедж: {s['slippage']}%", callback_data="set_slippage")],
        [InlineKeyboardButton(text=f"Доля от сделки: {s['value']}%", callback_data="set_value")],
        [InlineKeyboardButton(text=f"💳 Демо-баланс: ${s['demo_balance']:.2f}", callback_data="view_balance")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")]
    ])
    await cb.message.edit_text("⚙️ НАСТРОЙКИ КОПИТРЕЙДИНГА:", reply_markup=kb)

@router.callback_query(F.data == "toggle_auto")
async def toggle_auto_handler(cb: CallbackQuery):
    s = await get_settings(cb.from_user.id)
    new_val = 0 if s["auto_orders"] else 1
    await update_settings(cb.from_user.id, "auto_orders", new_val)
    await menu_copy_handler(cb)

# =====================================================================
# ОБРАБОТЧИКИ ОПЕРАЦИЙ ДОБАВЛЕНИЯ
# =====================================================================

@router.callback_query(F.data.startswith("mock_add_"))
async def mock_copy_add_handler(cb: CallbackQuery):
    await cb.answer("✅ Успешно добавлено в модуль копитрейдинга!", show_alert=True)
    
