import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)
router = Router()

# =====================================================================
# 1. ГЛАВНАЯ КЛАВИАТУРА И МЕНЮ (ПОД POLYMARKET)
# =====================================================================

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск кошельков", callback_data="menu_search")],
        [InlineKeyboardButton(text="🔄 Копитрейдинг", callback_data="menu_copy")]
    ])

@router.message(F.text == "/start")
async def start_cmd(message: Message):
    logger.info(f"User {message.from_user.id} triggered /start")
    welcome_text = (
        "👋 Добро пожаловать в Polymarket Trading Suite Бот!\n\n"
        "Система готова к работе под ключ. Управляйте настройками копирования "
        "или ищите прибыльные кошельки с помощью аналитических модулей."
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@router.callback_query(F.data == "menu_main")
async def back_to_main_menu_handler(cb: CallbackQuery):
    await cb.answer()
    welcome_text = (
        "👋 Главное меню Polymarket Trading Suite!\n\n"
        "Выберите нужный модуль для работы:"
    )
    await cb.message.edit_text(welcome_text, reply_markup=get_main_keyboard())

# =====================================================================
# 2. МОДУЛЬ ПОИСКА КОШЕЛЬКОВ
# =====================================================================

def get_search_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Топ трейдеры", callback_data="search_top")],
        [InlineKeyboardButton(text="🐋 Активность китов", callback_data="search_whales")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu_main")]
    ])

@router.callback_query(F.data == "menu_search")
async def menu_search_handler(cb: CallbackQuery):
    await cb.answer()
    await cb.message.edit_text(
        "🔍 Модуль поиска кошельков активирован!\n\n"
        "Выберите категорию для анализа рынков Polymarket:",
        reply_markup=get_search_keyboard()
    )

@router.callback_query(F.data.startswith("search_"))
async def search_actions_handler(cb: CallbackQuery):
    action = cb.data.split("_")[1]
    await cb.answer(f"Запущен поиск: {action}", show_alert=True)

# =====================================================================
# 3. МОДУЛЬ КОПИТРЕЙДИНГА
# =====================================================================

def get_copy_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Настройки ордеров", callback_data="copy_config")],
        [InlineKeyboardButton(text="📊 Демо-баланс", callback_data="copy_balance")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu_main")]
    ])

@router.callback_query(F.data == "menu_copy")
async def menu_copy_handler(cb: CallbackQuery):
    await cb.answer()
    await cb.message.edit_text(
        "🔄 Модуль копитрейдинга активирован!\n\n"
        "Управляйте конфигурацией демо-сделок на Polymarket:",
        reply_markup=get_copy_keyboard()
    )

@router.callback_query(F.data.startswith("copy_"))
async def copy_actions_handler(cb: CallbackQuery):
    action = cb.data.split("_")[1]
    await cb.answer(f"Открыт раздел: {action}", show_alert=True)
    
