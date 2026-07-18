from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

try:
    from database import get_settings, update_settings
except ImportError:
    pass

router = Router()

# ==========================================
# 1. ГЛАВНАЯ КЛАВИАТУРА
# ==========================================
def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск кошельков", callback_data="menu_search")],
        [InlineKeyboardButton(text="🔄 Копитрейдинг", callback_data="menu_copy")]
    ])

# ==========================================
# 2. ОБРАБОТКА КОМАНДЫ /START И ГЛАВНОГО МЕНЮ
# ==========================================
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
    await cb.answer()
    await cb.message.edit_text("Выберите нужный инструмент:", reply_markup=get_main_keyboard())

# ==========================================
# 3. ОБРАБОТКА НАЖАТИЙ НА КНОПКИ МОДУЛЕЙ
# ==========================================
@router.callback_query(F.data == "menu_search")
async def menu_search_handler(cb: CallbackQuery):
    await cb.answer() 
    await cb.message.edit_text("🔍 Модуль поиска кошельков активирован! Выберите категорию.")

@router.callback_query(F.data == "menu_copy")
async def menu_copy_handler(cb: CallbackQuery):
    await cb.answer()
    await cb.message.edit_text("🔄 Модуль копитрейдинга активирован! Настройки загружаются...")
    
