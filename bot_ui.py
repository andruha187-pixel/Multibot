import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database import get_settings, update_settings, add_to_copytrading, get_active_copy_wallets
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
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Добро пожаловать в Polymarket Trading Suite Бот!\nВыберите нужный инструмент:", 
        reply_markup=get_main_keyboard()
    )

@router.callback_query(F.data == "menu_main")
async def menu_main_handler(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.answer()
    await cb.message.edit_text("Выберите нужный инструмент:", reply_markup=get_main_keyboard())

# =====================================================================
# ВЫБОР КАТЕГОРИЙ И СТРАТЕГИЙ
# =====================================================================

@router.callback_query(F.data == "menu_search")
async def menu_search_handler(cb: CallbackQuery, state: FSMContext):
    await state.clear()
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
async def category_handler(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.answer()
    
    category = cb.data.replace("cat_", "").strip().lower()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 АВТОПОИСК (Идеальный фильтр)", callback_data=f"view:auto:{category}")],
        [InlineKeyboardButton(text="🔥 ФЛИП (Разгон $100)", callback_data=f"view:flip:{category}")],
        [InlineKeyboardButton(text="📊 Топ PnL", callback_data=f"view:pnl:{category}"), InlineKeyboardButton(text="🎯 Топ Winrate", callback_data=f"view:wr:{category}")],
        [InlineKeyboardButton(text="🔙 К категориям", callback_data="menu_search")]
    ])
    await cb.message.edit_text(f"Категория: {category.upper()}\nВыберите стратегию поиска:", reply_markup=kb)

# =====================================================================
# БОЕВОЙ ОБРАБОТЧИК КНОПОК ПОИСКА С РЕАЛЬНЫМ API
# =====================================================================

@router.callback_query(F.data.startswith("view:"))
async def execute_strategy(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    # Информируем пользователя о начале живого сканирования рынка
    await cb.message.edit_text("⏳ *Сканирую Polymarket API и Polygonscan... Пожалуйста, подождите.*", parse_mode="Markdown")
    await cb.answer()
    
    try:
        parts = cb.data.split(":")
        strategy_type = parts[1].strip().lower()
        category = parts[2].strip().lower()
        
        # Вызываем асинхронный парсер для получения реальных кошельков из сети
        wallets = await fetch_real_wallets(category, strategy_type)
        
        if not wallets:
            kb_error = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data=f"cat_{category}")]])
            await cb.message.edit_text("❌ В данный момент не удалось получить данные от Polymarket API или подходящие кошельки не найдены.", reply_markup=kb_error)
            return
        
        headers = {
            "flip": f"🔥 **РЕАЛЬНЫЕ РЕЗУЛЬТАТЫ «ФЛИП» ({category.upper()})**\n\n",
            "auto": f"🤖 **ЖИВОЙ АВТОПОИСК ({category.upper()})**\n\n",
            "pnl": f"📊 **ГЛОБАЛЬНЫЙ ЛИДЕРБОРД ПО PnL ({category.upper()})**\n\n",
            "wr": f"🎯 **ТОП WINRATE КОШЕЛЬКИ С РЫНКА ({category.upper()})**\n\n"
        }
        
        report = headers.get(strategy_type, f"📋 **СПИСОК КОШЕЛЬКОВ ({category.upper()})**\n\n")
        
        kb_list = []
        row = []
        temp_wallet_map = {}
        
        for i, w in enumerate(wallets, 1):
            if strategy_type == "flip":
                report += f"{i}. 👤 `{w['name']}`\n   • Вход: {w['price']} (Потенциал: {w['pot']})\n   • `{w['address']}`\n\n"
            elif strategy_type == "auto":
                report += f"{i}. 👤 `{w['name']}`\n   • {w['metric']}\n   • `{w['address']}`\n\n"
            else:
                report += f"{i}. 👤 `{w['name']}`\n   • {w['metric']}\n   • `{w['address']}`\n\n"
                
            short_id = w['address'][-8:]
            temp_wallet_map[short_id] = w['address']
            
            row.append(InlineKeyboardButton(text=f"➕ Копи #{i}", callback_data=f"addcopy_{w['name']}_{short_id}"))
            if len(row) == 2:
                kb_list.append(row)
                row = []
                
        if row:
            kb_list.append(row)

        # Сохраняем реальные адреса в FSM-state для защиты от frozen instance ошибок
        await state.update_data(wallet_map=temp_wallet_map)

        kb_list.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"cat_{category}")])
        await cb.message.edit_text(report, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_list), parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка в execute_strategy: {e}", exc_info=True)
        await cb.message.answer(f"⚠️ Произошла ошибка при обработке данных: {str(e)}")

# =====================================================================
# МОДУЛЬ КОПИТРЕЙДИНГА 
# =====================================================================

@router.callback_query(F.data == "menu_copy")
async def menu_copy_handler(cb: CallbackQuery, state: FSMContext):
    await state.clear()
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
async def view_active_wallets_handler(cb: CallbackQuery, state: FSMContext):
    await state.clear()
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
    await cb.message.answer("📥 Отправьте в чат Polygon адрес кошелька Polymarket, который вы хотите копировать:")

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
async def add_to_copy_callback(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split("_")
    name = parts[1]
    short_hash = parts[2]
    
    # Извлекаем безопасный сохраненный адрес из состояния
    user_data = await state.get_data()
    wallet_map = user_data.get("wallet_map", {})
    full_address = wallet_map.get(short_hash, "0xНеизвестно")
    
    await add_to_copytrading(cb.from_user.id, name, full_address)
    await cb.answer(f"✅ {name} добавлен в копитрейдинг!", show_alert=True)

@router.callback_query(F.data == "toggle_auto")
async def toggle_auto_handler(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    s = await get_settings(cb.from_user.id)
    new_val = 0 if s["auto_orders"] else 1
    await update_settings(cb.from_user.id, "auto_orders", new_val)
    await menu_copy_handler(cb, state)
    
