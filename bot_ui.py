import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import get_settings, update_settings

logger = logging.getLogger(__name__)
router = Router()

# =====================================================================
# ГЛАВНОЕ МЕНЮ И СТАРТ
# =====================================================================

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
# МОДУЛЬ ПОИСКА: ТВОИ 7 КАТЕГОРИЙ POLYMARKET
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

# =====================================================================
# ТВОЙ КОД: МЕНЮ ВНУТРИ КАТЕГОРИИ (Исправлен синтаксис callback_data)
# =====================================================================

@router.callback_query(F.data.startswith("cat_"))
async def category_handler(cb: CallbackQuery):
    await cb.answer()  # Убирает зависание кнопки
    category = cb.data.split("_")[1]
    
    # Исправлено: callback_query_data -> callback_data
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 АВТОПОИСК (Идеальный фильтр)", callback_data=f"autosearch_{category}")],
        [InlineKeyboardButton(text="🔥 ФЛИП (Разгон $100)", callback_data=f"flipsearch_{category}")],
        [InlineKeyboardButton(text="📊 Топ PnL", callback_data=f"filter_pnl_{category}"), 
         InlineKeyboardButton(text="🎯 Топ Winrate", callback_data=f"filter_wr_{category}")],
        [InlineKeyboardButton(text="🔙 К категориям", callback_data="menu_search")]
    ])
    await cb.message.edit_text(f"Категория: {category.upper()}\nВыберите стратегию поиска:", reply_markup=kb)

# =====================================================================
# ТВОЙ КОД: ОБРАБОТЧИК КНОПКИ ФЛИП (Вывод отчета со снайперами)
# =====================================================================

@router.callback_query(F.data.startswith("flipsearch_"))
async def flipsearch_execute(cb: CallbackQuery):
    category = cb.data.split("_")[1]
    await cb.answer("Ищу снайперов копеечных исходов...")
    
    report = (
        f"🔥 **РЕЗУЛЬТАТЫ СКАНИРОВАНИЯ «ФЛИП» ({category.upper()})**\n"
        f"Кошельки для разгона малого депозита. Ищут исходы по $0.05-$0.25 с потенциалом от 5x до 20x:\n\n"
        f"1. 👤 `Penny_Sniper_42` (0x9b...e77)\n"
        f"   • Средняя цена входа: $0.12 (Потенциал: 8.3x)\n"
        f"   • Истинный ROI: +240% при винрейте 35%\n"
        f"   • Идеально для ордеров по $5-$10\n\n"
        f"2. 👤 `Insider_LowCap` (0x11...fa4)\n"
        f"   • Средняя цена входа: $0.08 (Потенциал: 12.5x)\n"
        f"   • Замечает резкие изменения вероятностей до апдейта новостей\n"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Копировать Sniper_42", callback_data="mock_add_flip1")],
        [InlineKeyboardButton(text="➕ Копировать Insider", callback_data="mock_add_flip2")],
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
# ЗАГЛУШКИ ДЛЯ ОСТАЛЬНЫХ КНОПОК
# =====================================================================

@router.callback_query(F.data.startswith("autosearch_"))
@router.callback_query(F.data.startswith("filter_"))
async def mock_filters_handler(cb: CallbackQuery):
    action = cb.data.split("_")[0]
    await cb.answer(f"Запуск фильтра {action}. Идёт сбор статистики...", show_alert=True)

@router.callback_query(F.data.startswith("mock_add_"))
async def mock_copy_add_handler(cb: CallbackQuery):
    await cb.answer("✅ Кошелек успешно добавлен в модуль копитрейдинга!", show_alert=True)
    
