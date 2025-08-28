# handlers/choose_rag.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from db.repos.active_rag_repo import ActiveRagSourceRepo


async def choose_rag_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /choose_rag"""
    user_id = update.effective_user.id

    # Получаем репозиторий активных RAG-источников из глобальных данных бота
    active_rag_repo: ActiveRagSourceRepo = context.bot_data['active_rag_repo']

    sources = active_rag_repo.get_all_sources()

    if not sources:
        await update.message.reply_text(
            "❌ В системе пока нет доступных RAG источников.\n"
            "Добавьте новый источник с помощью команды /add_rag_source"
        )
        return

    keyboard = []
    for source in sources:
        keyboard.append([InlineKeyboardButton(
            f"{source.name}",
            callback_data=f"choose_rag_{source.id}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📚 Выберите RAG источник для работы:",
        reply_markup=reply_markup
    )


async def choose_rag_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора RAG источника"""
    query = update.callback_query
    user_id = update.effective_user.id

    source_id = query.data.replace("choose_rag_", "")

    active_rag_repo: ActiveRagSourceRepo = context.bot_data['active_rag_repo']
    active_rag_repo.set_active_source(user_id, source_id)

    source = active_rag_repo.get_active_source(user_id)

    await query.answer()
    await query.edit_message_text(
        f"✅ Выбран источник: {source.name}\n"
        "Теперь вы можете начать диалог командой /qviz"
    )
