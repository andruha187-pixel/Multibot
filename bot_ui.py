from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# Если роутер регистрируется здесь, оставляем его. 
# Если нет — этот импорт базы данных можно убрать/оставить по ситуации.
try:
    from database import get_settings, update_settings
except ImportError:
    pass

router = Router()

# ==========================================
# КЛАВИАТУРЫ И МЕНЮ (ИСПРАВЛЕНО)
# ==========================================

def get_main_keyboard():
    # Исправленная клавиатура: у каждой кнопки ЕСТЬ callback_data вместо простого текста
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск кошельков", callback_data="menu_search")],
        [InlineKeyboardButton(text="🔄 Копитрейдинг", callback_data="menu_copy")]
    ])

# ==========================================
# ГЛАВНЫЕ КОМАНДЫ
# ==========================================

@router.message(Command("start", ignore_case=True))
async def start_cmd(message: Message):
    welcome_text = (
        "👋 Добро пожаловать в Polymarket Trading Suite Бот!\n\n"
        "Система готова к работе под ключ. Управляйте настройками копирования "
        "или ищите прибыльные кошельки с помощью аналитических модулей."
    )
    # Вызываем исправленную функцию
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@router.callback_query(F.data == "menu_main")
async def menu_main_handler(cb: CallbackQuery):
    await cb.message.edit_text("Выберите нужный инструмент:", reply_markup=get_main_keyboard())
    
