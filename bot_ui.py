@router.callback_query(F.data.startswith("cat_"))
async def category_handler(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.answer()
    
    # Принудительно очищаем строку и переводим в нижний регистр
    category = cb.data.replace("cat_", "").strip().lower()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 АВТОПОИСК (Идеальный фильтр)", callback_data=f"view:auto:{category}")],
        [InlineKeyboardButton(text="🔥 ФЛИП (Разгон $100)", callback_data=f"view:flip:{category}")],
        [InlineKeyboardButton(text="📊 Топ PnL", callback_data=f"view:pnl:{category}"), InlineKeyboardButton(text="🎯 Топ Winrate", callback_data=f"view:wr:{category}")],
        [InlineKeyboardButton(text="🔙 К категориям", callback_data="menu_search")]
    ])
    await cb.message.edit_text(f"Категория: {category.upper()}\nВыберите стратегию поиска:", reply_markup=kb)

@router.callback_query(F.data.startswith("view:"))
async def execute_strategy(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.answer()
    
    try:
        parts = cb.data.split(":")
        strategy_type = parts[1].strip().lower() # auto, flip, pnl, wr
        category = parts[2].strip().lower()      # crypto, politics, etc.
        
        # Защитная проверка на существование категории в словаре
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
        
        if not hasattr(cb.message, 'conf') or cb.message.conf is None:
            cb.message.conf = {}
            
        kb_list = []
        row = []
        
        for i, w in enumerate(wallets, 1):
            if strategy_type == "flip":
                report += f"{i}. 👤 `{w['name']}`\n   • Вход: {w['price']} (Потенциал: {w['pot']})\n   • `{w['address']}`\n\n"
            elif strategy_type == "auto":
                report += f"{i}. 👤 `{w['name']}`\n   • Метрики: {w['metric']}\n   • `{w['address']}`\n\n"
            else:
                report += f"{i}. 👤 `{w['name']}`: {w['metric']}\n   • `{w['address']}`\n\n"
                
            short_id = w['address'][-8:]
            cb.message.conf[short_id] = w['address']
            
            row.append(InlineKeyboardButton(text=f"➕ Копи #{i}", callback_data=f"addcopy_{w['name']}_{short_id}"))
            if len(row) == 2:
                kb_list.append(row)
                row = []
                
        if row:
            kb_list.append(row)

        kb_list.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"cat_{category}")])
        await cb.message.edit_text(report, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_list), parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка в execute_strategy: {e}", exc_info=True)
        await cb.message.answer(f"⚠️ Произошла ошибка при генерации списка кошельков: {str(e)}")
    
