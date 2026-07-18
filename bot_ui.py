import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)
router = Router()

# =====================================================================
# ГЛАВНЫЕ КЛАВИАТУРЫ И ХЭНДЛЕРЫ МЕНЮ
# =====================================================================

def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск кошельков", callback_data="menu_search")],
        [InlineKeyboardButton(text="🔄 Копитрейдинг", callback_data="menu_copy")],
        [InlineKeyboardButton(text="💰 Профиль / Подписка", callback_data="menu_profile")]
    ])

@router.message(F.text == "/start")
async def start_command_handler(msg: Message):
    logger.info(f"User {msg.from_user.id} triggered /start")
    await msg.answer(
        "👋 Добро пожаловать в AlphaRadar Bot!\n\n"
        "Я помогу тебе находить прибыльные кошельки на Solana и автоматически копировать их сделки.\n\n"
        "Выберите нужное действие на клавиатуре ниже:",
        reply_markup=main_menu_keyboard()
    )

@router.callback_query(F.data == "menu_main")
async def back_to_main_menu_handler(cb: CallbackQuery):
    await cb.answer()
    await cb.message.edit_text(
        "👋 Главное меню AlphaRadar Bot.\n\n"
        "Выберите нужный модуль для работы:",
        reply_markup=main_menu_keyboard()
    )

# =====================================================================
# МОДУЛЬ 1: ПОИСК КОШЕЛЬКОВ
# =====================================================================

def get_search_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Топ по винрейту", callback_data="search_winrate")],
        [InlineKeyboardButton(text="🐋 Слежка за китами", callback_data="search_whales")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu_main")]
    ])

@router.callback_query(F.data == "menu_search")
async def menu_search_handler(cb: CallbackQuery):
    await cb.answer()
    # Теперь здесь передается клавиатура get_search_keyboard()
    await cb.message.edit_text(
        "🔍 Модуль поиска кошельков активирован!\n\n"
        "Выберите категорию для анализа или вернитесь назад:",
        reply_markup=get_search_keyboard()
    )

@router.callback_query(F.data.startswith("search_"))
async def search_actions_handler(cb: CallbackQuery):
    # Заглушка для обработки подкатегорий поиска
    action = cb.data.split("_")[1]
    await cb.answer(f"Запущен режим: {action}", show_alert=True)
    # Сюда позже добавим логику парсинга или вывода результатов

# =====================================================================
# МОДУЛЬ 2: КОПИТРЕЙДИНГ
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
    # Теперь здесь передается клавиатура get_copy_keyboard()
    await cb.message.edit_text(
        "🔄 Модуль копитрейдинга активирован!\n\n"
        "Управляйте конфигурацией сделок и проверяйте балансы:",
        reply_markup=get_copy_keyboard()
    )

@router.callback_query(F.data.startswith("copy_"))
async def copy_actions_handler(cb: CallbackQuery):
    # Заглушка для обработки подкатегорий копитрейдинга
    action = cb.data.split("_")[1]
    await cb.answer(f"Открыт раздел: {action}", show_alert=True)

# =====================================================================
# МОДУЛЬ 3: ПРОФИЛЬ И ПОДПИСКА
# =====================================================================

@router.callback_query(F.data == "menu_profile")
async def menu_profile_handler(cb: CallbackQuery):
    await cb.answer()
    # Клавиатура возврата для меню профиля
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu_main")]
    ])
    await cb.message.edit_text(
        "👤 **Ваш профиль:**\n"
        "├ ID: `{}`\n"
        "└ Статус: **FREE (Базовый)**\n\n"
        "💳 Подписка активна до: Неограниченно".format(cb.from_user.id),
        parse_mode="Markdown",
        reply_markup=back_kb
    )
    
