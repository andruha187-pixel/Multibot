import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database import get_settings, update_settings, add_to_copytrading, get_active_copy_wallets

logger = logging.getLogger(__name__)
router = Router()

class CopyStates(StatesGroup):
    input_address = State()

# =====================================================================
# ГЕНЕРАТОР УНИКАЛЬНЫХ ДАННЫХ ДЛЯ КАЖДОЙ КАТЕГОРИИ
# =====================================================================
def generate_mock_wallets(category, search_type):
    wallets = []
    multipliers = {
        "crypto": {"pnl": 2.5, "wr": 12, "price": 0.50},
        "politics": {"pnl": 1.8, "wr": 5, "price": 0.20},
        "sports": {"pnl": 1.2, "wr": 8, "price": 0.15},
        "esports": {"pnl": 0.9, "wr": 2, "price": 0.08},
        "finance": {"pnl": 3.0, "wr": 15, "price": 0.80},
        "economy": {"pnl": 1.5, "wr": 4, "price": 0.35},
        "weather": {"pnl": 0.4, "wr": 1, "price": 0.05}
    }
    mult = multipliers.get(category, {"pnl": 1.0, "wr": 5, "price": 0.10})
    
    for i in range(1, 21):
        if search_type == "flip":
            price_val = mult["price"] + (i * 0.02)
            pot_val = max(25.0 - (i * 0.9) - mult["wr"], 1.5)
            wallets.append({
                "name": f"Sniper_{category}_{i}",
                "address": f"0x{i:02d}F11P{i:02d}7777777777777777777777777{i:02d}aa",
                "price": f"${price_val:.2f}",
                "pot": f"{pot_val:.1f}x"
            })
        elif search_type == "auto":
            wr = max(55 + (i * 2) - mult["wr"], 40)
            profit = int((2000 + (i * 400)) * mult["pnl"])
            wallets.append({
                "name": f"Auto_{category}_{i}",
                "address": f"0x{i:02d}4UT0{i:02d}8888888888888888888888888{i:02d}bb",
                "metric": f"WR {wr}%, +${profit:,}"
            })
        elif search_type == "pnl":
            wr = max(78 - i, 50)
            profit = int((160000 - (i * 6500)) * mult["pnl"])
            wallets.append({
                "name": f"Whale_{category}_{i}",
                "address": f"0x{i:02d}PN1{i:02d}9999999999999999999999999{i:02d}cc",
                "metric": f"+${profit:,} (WR: {wr}%)"
            })
        elif search_type == "wr":
            wr = max(95 - (i // 2) - (mult["wr"] // 3), 60)
            profit = int((6000 - (i * 250)) * mult["pnl"])
            wallets.append({
                "name": f"Alpha_{category}_{i}",
                "address": f"0x{i:02d}WRR{i:02d}1111111111111111111111111{i:02d}dd",
                "metric": f"WR {wr}% (+${profit:,})"
            })
    return wallets

MARKET_DATA = {}
for cat in ["crypto", "politics", "sports", "esports", "finance", "economy", "weather"]:
    MARKET_DATA[cat] = {
        "flip": generate_mock_wallets(cat, "flip"),
        "auto": generate_mock_wallets(cat, "auto"),
        "pnl": generate_mock_wallets(cat, "pnl"),
        "wr": generate_mock_wallets(cat, "wr")
    }

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск кошельков", callback_data="menu_search")],
        [InlineKeyboardButton(text="🔄 Копитрейдинг", callback_data="menu_copy")]
    ])

@router.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("👋 Добро пожаловать в Polymarket Trading Suite Бот!\nВыберите нужный инструмент:", reply_markup=get_main_keyboard())

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
# ИСПРАВЛЕННЫЙ ОБРАБОТЧИК КНОПОК ПОИСКА (БЕЗ ИЗМЕНЕНИЯ MESSAGE)
# =====================================================================

@router.callback_query(F.data.startswith("view:"))
async def execute_strategy(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.answer()
    
    try:
        parts = cb.data.split(":")
        strategy_type = parts[1].strip().lower()
        category = parts[2].strip().lower()
        
        if category not in MARKET_DATA:
            await cb.message.answer(f"❌ Категория '{category}' не найдена в базе данных.")
            return
            
        if strategy_type not in MARKET_DATA[category]:
            await cb.message.answer(f"❌ Стратегия '{strategy_type}' не найдена для этой категории.")
            return
            
        wallets = MARKET_DATA[category][strategy_type]
        
        headers = {
            "flip": f"🔥 **РЕЗУЛЬТАТЫ «ФЛИП» ({category.upper()})**\n\n",
            "auto": f"🤖 **АВТОПОИСК ({category.upper()})**\n\n",
            "pnl": f"📊 **ЛИДЕРБОРД ПО PnL ({category.upper()})**\n\n",
            "wr": f"🎯 **СТАБИЛЬНЫЕ WINRATE КОШЕЛЬКИ ({category.upper()})**\n\n"
        }
        
        report = headers.get(strategy_type, f"📋 **СПИСОК КОШЕЛЬКОВ ({category.upper()})**\n\n")
        
        kb_list = []
        row = []
        
        # Вместо message.conf сохраняем хэши адресов в FSM-state данные
        temp_wallet_map = {}
        
        for i, w in enumerate(wallets, 1):
            if strategy_type == "flip":
                report += f"{i}. 👤 `{w['name']}`\n   • Вход: {w['price']} (Потенциал: {w['pot']})\n   • `{w['address']}`\n\n"
            elif strategy_type == "auto":
                report += f"{i}. 👤 `{w['name']}`\n   • Метрики: {w['metric']}\n   • `{w['address']}`\n\n"
            else:
                report += f"{i}. 👤 `{w['name']}`: {w['metric']}\n   • `{w['address']}`\n\n"
                
            short_id = w['address'][-8:]
            temp_wallet_map[short_id] = w['address']
            
            row.append(InlineKeyboardButton(text=f"➕ Копи #{i}", callback_data=f"addcopy_{w['name']}_{short_id}"))
            if len(row) == 2:
                kb_list.append(row)
                row = []
                
        if row:
            kb_list.append(row)

        # Сохраняем сгенерированную карту адресов в state
        await state.update_data(wallet_map=temp_wallet_map)

        kb_list.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"cat_{category}")])
        await cb.message.edit_text(report, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_list), parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка в execute_strategy: {e}", exc_info=True)
        await cb.message.answer(f"⚠️ Произошла ошибка при генерации списка кошельков: {str(e)}")

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

# Обновленное добавление в копирование через FSM-data
@router.callback_query(F.data.startswith("addcopy_"))
async def add_to_copy_callback(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split("_")
    name = parts[1]
    short_hash = parts[2]
    
    # Достаем карту адресов из безопасного контекста FSM
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
    
