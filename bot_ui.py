import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)
router = Router()

# =====================================================================
# ГЛАВНОЕ МЕНЮ И СТАРТ
# =====================================================================

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск кошельков", callback_data="menu_search")],
        [InlineKeyboardButton(text="🔄 Копитрейдинг", callback_data="menu_copy")],
        [InlineKeyboardButton(text="💰 Профиль / Подписка", callback_data="menu_profile")]
    ])

@router.message(F.text == "/start")
async def start_cmd(message: Message):
    logger.info(f"User {message.from_user.id} triggered /start")
    await message.answer(
        "👋 Добро пожаловать!\n\nВыберите нужный модуль для работы:",
        reply_markup=get_main_keyboard()
    )

@router.callback_query(F.data == "menu_main")
async def back_to_main_menu_handler(cb: CallbackQuery):
    await cb.answer()
    await cb.message.edit_text(
        "👋 Главное меню.\n\nВыберите нужный модуль для работы:",
        reply_markup=get_main_keyboard()
    )

# =====================================================================
# МОДУЛЬ ПОИСКА И КАТЕГОРИИ
# =====================================================================

def get_search_categories_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        # Передаем cat_top и cat_whales, чтобы попасть в меню стратегий
        [InlineKeyboardButton(text="🔥 Топ трейдеры", callback_data="cat_top")],
        [InlineKeyboardButton(text="🐋 Активность китов", callback_data="cat_whales")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu_main")]
    ])

@router.callback_query(F.data == "menu_search")
async def menu_search_handler(cb: CallbackQuery):
    await cb.answer()
    await cb.message.edit_text(
        "🔍 Модуль поиска кошельков активирован!\n\n"
        "Выберите категорию для анализа рынков Polymarket:",
        reply_markup=get_search_categories_keyboard()
    )

# Твой первичный хэндлер (исправлена ошибка callback_query_data -> callback_data)
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
# СТРАТЕГИИ ПОИСКА (ФЛИП / АВТОПОИСК / ФИЛЬТРЫ)
# =====================================================================

# Твой обработчик кнопки Флип
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

# Заглушки для автопоиска и остальных фильтров, чтобы бот не зависал при нажатии
@router.callback_query(F.data.startswith("autosearch_"))
@router.callback_query(F.data.startswith("filter_"))
async def mock_filters_handler(cb: CallbackQuery):
    action = cb.data.split("_")[0]
    await cb.answer(f"Запуск фильтра: {action}. Поиск активен...", show_alert=True)

@router.callback_query(F.data.startswith("mock_add_"))
async def mock_copy_add_handler(cb: CallbackQuery):
    await cb.answer("✅ Кошелек успешно добавлен в модуль копитрейдинга!", show_alert=True)

# =====================================================================
# ОСТАЛЬНЫЕ МОДУЛИ (КОПИТРЕЙДИНГ И ПРОФИЛЬ)
# =====================================================================

@router.callback_query(F.data == "menu_copy")
async def menu_copy_handler(cb: CallbackQuery):
    await cb.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu_main")]
    ])
    await cb.message.edit_text("🔄 Модуль копитрейдинга в разработке.", reply_markup=kb)

@router.callback_query(F.data == "menu_profile")
async def menu_profile_handler(cb: CallbackQuery):
    await cb.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu_main")]
    ])
    await cb.message.edit_text("💰 Профиль и подписка: статус FREE.", reply_markup=kb)
