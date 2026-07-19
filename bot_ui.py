import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database import get_settings, update_settings, add_to_copytrading, get_active_copy_wallets
# Импортируем наш рабочий парсер (который мы переписали на aiohttp)
from parser import fetch_real_wallets

logger = logging.getLogger(__name__)
router = Router()

class CopyStates(StatesGroup):
    input_address = State()

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск кошельков", callback_data="menu_search")],
        [InlineKeyboardButton(text="🔄 Копитрейдинг", callback_data="menu_copy")]
    ])

@router.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("👋 Добро пожаловать в Polymarket Trading Suite Бот!\nВыберите нужный инструмент:", reply_markup=get_main_keyboard())

@router.callback_query(F.data == "menu_main")
async def menu_main_handler(cb: CallbackQuery):
    await cb.answer()
    await cb.message.edit_text("Выберите нужный инструмент:", reply_markup=get_main_keyboard())

# =====================================================================
# МОДУЛЬ ПОИСКА И СКАНИРОВАНИЯ
# =====================================================================

@router.callback_query(F.data == "menu_search")
async def menu_search_handler(cb: CallbackQuery):
    await cb.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪙 Крипта", callback_data="cat_crypto"), InlineKeyboardButton(text="🏛 Политика", callback_data="cat_politics")],
        [InlineKeyboardButton(text="⚽️ Спорт LIVE", callback_data="cat_sports"), InlineKeyboardButton(text="🎮 Киберспорт", callback_data="cat_esports")],
        [InlineKeyboardButton(text="📈 Финансы", callback_data="cat_finance"), InlineKeyboardButton(text="📊 Экономика", callback_data="cat_economy")],
        [InlineKeyboardButton(text="☀️ Погода", callback_data="cat_weather")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")]
    ])
    await cb.message.edit_text("🔍 Выберите категорию Polymarket для аналитики кошельков:", reply_markup=kb)

@router.callback_query(F.data.startswith("cat_"))
async def category_handler(cb: CallbackQuery):
    await cb.answer()
    category = cb.data.split("_")[1]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 АВТОПОИСК (Идеальный фильтр)", callback_data=f"search_auto_{category}")],
        [InlineKeyboardButton(text="🔥 ФЛИП (Разгон $100)", callback_data=f"search_flip_{category}")],
        [InlineKeyboardButton(text="📊 Топ PnL", callback_data=f"search_pnl_{category}"), InlineKeyboardButton(text="🎯 Топ Winrate", callback_data=f"search_wr_{category}")],
        [InlineKeyboardButton(text="🔙 К категориям", callback_data="menu_search")]
    ])
    await cb.message.edit_text(f"Категория: {category.upper()}\nВыберите стратегию поиска:", reply_markup=kb)

# =====================================================================
# ДИНАМИЧЕСКИЙ ВЫВОД РЕАЛЬНЫХ ДАННЫХ ИЗ ПАРСЕРА
# =====================================================================

@router.callback_query(F.data.startswith("search_"))
async def execute_search_handler(cb: CallbackQuery):
    # Формат callback_data: search_тип_категория (например: search_auto_crypto)
    parts = cb.data.split("_")
    strategy_type = parts[1]
    category = parts[2]
    
    await cb.answer("Загрузка данных из Polymarket API...", show_alert=False)
    
    # Запрашиваем живые данные через наш парсер
    wallets = await fetch_real_wallets(category, strategy_type)
    
    # Задаем заголовки для разных режимов
    titles = {
        "auto": f"🤖 **АВТОПОИСК ({category.upper()})**\nФильтр по стабильности и объему:\n\n",
        "flip": f"🔥 **СТРАТЕГИЯ «ФЛИП» ({category.upper()})**\nРазгон баланса на мелких исходах:\n\n",
        "pnl": f"📊 **ЛИДЕРБОРД ПО PnL ({category.upper()})**\nСамые прибыльные кошельки:\n\n",
        "wr": f"🎯 **ЛИДЕРБОРД ПО WINRATE ({category.upper()})**\nМаксимальный процент побед:\n\n"
    }
    
    report = titles.get(strategy_type, f"📋 **Результаты ({category.upper()}):**\n\n")
    
    if not wallets:
        report += "❌ Не удалось получить данные или кошельки не соответствуют фильтрам стратегии в данный момент."
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data=f"cat_{category}")]])
        await cb.message.edit_text(report, reply_markup=kb, parse_mode="Markdown")
        return

    # Инициализируем хранилище адресов в контексте сообщения, чтобы кнопки могли их прочитать
    cb.message.conf = cb.message.conf if hasattr(cb.message, 'conf') else {}
    kb_list = []
    row = []
    
    for i, w in enumerate(wallets, 1):
        name = w.get("name", f"Trader_{i}")
        address = w.get("address", "0x")
        
        # Собираем красивую метрику в зависимости от того, что вернул парсер
        if "price" in w and "pot" in w:
            metric_line = f"Вход: {w['price']} | Потенциал: {w['pot']}"
        else:
            metric_line = w.get("metric", "Активен")
            
        report += f"{i}. 👤 `{name}`\n   • {metric_line}\n   • `{address}`\n\n"
        
        # Генерируем короткий хэш для callback кнопки (ограничение Telegram на длину данных в кнопке)
        short_id = address[-8:]
        cb.message.conf[short_id] = address
        
        # Добавляем кнопку добавления в копитрейдинг
        row.append(InlineKeyboardButton(text=f"➕ Копировать #{i}", callback_data=f"addcopy_{name}_{short_id}"))
        if len(row) == 2:
            kb_list.append(row)
            row = []
            
    if row:
        kb_list.append(row)

    kb_list.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"cat_{category}")])
    await cb.message.edit_text(report, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_list), parse_mode="Markdown")

# =====================================================================
# УПРАВЛЕНИЕ КОПИТРЕЙДИНГОМ
# =====================================================================

@router.callback_query(F.data == "menu_copy")
async def menu_copy_handler(cb: CallbackQuery):
    await cb.answer()
    s = await get_settings(cb.from_user.id)
    auto_status = "🟢 ВКЛ" if s["auto_orders"] else "🔴 ВЫКЛ"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Авто-ордера: {auto_status}", callback_data="toggle_auto")],
        [InlineKeyboardButton(text="📋 Список кошельков на копировании", callback_data="view_active_wallets")],
        [InlineKeyboardButton(text="➕ Добавить адрес вручную", callback_data="add_manual_address")],
        [InlineKeyboardButton(text=f"Слиппедж: {s['slippage']}%", callback_data="set_slippage"),
         InlineKeyboardButton(text=f"Доля: {s['value']}%", callback_data="set_value")],
        [InlineKeyboardButton(text=f"💳 Демо-баланс: ${s['demo_balance']:.2f}", callback_data="view_balance")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")]
    ])
    await cb.message.edit_text("⚙️ НАСТРОЙКИ МОДУЛЯ КОПИТРЕЙДИНГА:", reply_markup=kb)

@router.callback_query(F.data == "view_active_wallets")
async def view_active_wallets_handler(cb: CallbackQuery):
    await cb.answer()
    wallets = await get_active_copy_wallets(cb.from_user.id)
    
    if not wallets:
        report = "📋 **Список кошельков пуст.**\nВы пока не добавили ни одного адреса для копирования ордеров."
    else:
        report = "📋 **Активные адреса в копитрейдинге:**\n\n"
        for i, w in enumerate(wallets, 1):
            report += f"{i}. Название: `{w['name']}`\n   Адрес: `{w['address']}`\n\n"
            
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="menu_copy")]])
    await cb.message.edit_text(report, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "add_manual_address")
async def add_manual_handler(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await state.set_state(CopyStates.input_address)
    await cb.message.answer("📥 Отправьте в чат Ethereum (Polygon) адрес кошелька, который вы хотите копировать:")

@router.message(CopyStates.input_address)
async def process_manual_address(message: Message, state: FSMContext):
    address = message.text.strip()
    if not address.startswith("0x") or len(address) != 42:
        await message.answer("❌ Неверный формат адреса. Он должен начинаться с 0x и состоять из 42 символов. Попробуйте еще раз:")
        return
        
    await add_to_copytrading(message.from_user.id, "Manual_Input", address)
    await state.clear()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⚙️ В настройки", callback_data="menu_copy")]])
    await message.answer(f"✅ Адрес успешно внесен в базу копитрейдинга!\n`{address}`", reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("addcopy_"))
async def add_to_copy_callback(cb: CallbackQuery):
    parts = cb.data.split("_")
    name = parts[1]
    short_hash = parts[2]
    
    full_address = cb.message.conf.get(short_hash, "0xНеизвестно") if hasattr(cb.message, 'conf') else "0xНеизвестно"
    
    await add_to_copytrading(cb.from_user.id, name, full_address)
    await cb.answer(f"✅ {name} добавлен в копитрейдинг!", show_alert=True)

@router.callback_query(F.data == "toggle_auto")
async def toggle_auto_handler(cb: CallbackQuery):
    s = await get_settings(cb.from_user.id)
    new_val = 0 if s["auto_orders"] else 1
    await update_settings(cb.from_user.id, "auto_orders", new_val)
    await menu_copy_handler(cb)
    
