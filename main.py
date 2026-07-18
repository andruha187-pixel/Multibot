from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

router = Router()

# ==========================================
# 1. ГЛАВНАЯ КЛАВИАТУРА (Проверено)
# ==========================================
def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск кошельков", callback_data="menu_search")],
        [InlineKeyboardButton(text="🔄 Копитрейдинг", callback_data="menu_copy")]
    ])

# ==========================================
# 2. ОБРАБОТКА КОМАНДЫ /START
# ==========================================
@router.message(Command("start", ignore_case=True))
async def start_cmd(message: Message):
    welcome_text = (
        "👋 Добро пожаловать в Polymarket Trading Suite Бот!\n\n"
        "Система готова к работе под ключ. Управляйте настройками копирования "
        "или ищите прибыльные кошельки с помощью аналитических модулей."
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

# ==========================================
# 3. ОБРАБОТКА НАЖАТИЙ НА КНОПКИ (Исправлено)
# ==========================================
@router.callback_query(F.data == "menu_search")
async def menu_search_handler(cb: CallbackQuery):
    # Обязательно гасим часики на кнопке
    await cb.answer() 
    
    # Отправляем тестовый ответ, чтобы убедиться, что переход работает
    await cb.message.edit_text("🔍 Модуль поиска кошельков активирован! Выберите категорию.")

@router.callback_query(F.data == "menu_copy")
async def menu_copy_handler(cb: CallbackQuery):
    await cb.answer()
    await cb.message.edit_text("🔄 Модуль копитрейдинга активирован! Настройки загружаются...")
