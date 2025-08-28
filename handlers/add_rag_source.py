import logging
import os
import tempfile
from typing import Optional, Any

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

for logger_name in ['httpcore', 'httpx', 'urllib3', 'asyncio', 'pyrogram', 'telethon']:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

logger = logging.getLogger('bot-latoken')
logger.setLevel(logging.INFO)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20,971,520 байт

# Состояния для ConversationHandler
WAITING_ARCHIVE = 1
END = ConversationHandler.END


async def add_rag_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /add_rag_source"""
    try:
        # Очищаем предыдущее состояние
        context.user_data.clear()
        # Устанавливаем флаг активного состояния
        context.user_data['waiting_for_archive'] = True

        user_id = update.effective_user.id
        logger.info(f"User {user_id} initiated RAG source addition")

        instructions = """
📚 Загрузите ZIP-архив с документами для создания базы знаний.

Поддерживаемые форматы файлов:
• PDF (*.pdf)
• Microsoft Word (*.doc, *.docx)
• Microsoft Excel (*.xls, *.xlsx)
• Текстовые файлы (*.txt)
• Json

⚠️ Убедитесь, что:
1. Все файлы упакованы в ZIP-архив
2. Размер архива не превышает 20MB
3. Файлы содержат текстовую информацию

Отправьте архив как документ...
"""
        await update.message.reply_text(instructions)
        logger.debug(f"Sent instructions to user {user_id}")
        return WAITING_ARCHIVE

    except Exception as e:
        logger.error(f"Error in add_rag_source: {e}", exc_info=True)
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
        return END


async def handle_other_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик других команд во время ожидания архива"""
    if context.user_data.get('waiting_for_archive'):
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Загрузка архива отменена из-за использования другой команды.\n"
            "Для повторной загрузки используйте /add_rag_source"
        )
    return END


async def handle_archive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик загрузки архива"""
    user_id = update.effective_user.id
    logger.info(f"Handling archive upload from user {user_id}")

    source: Optional[Any] = None
    temp_zip_path: Optional[str] = None

    try:
        if not update.message.document:
            logger.warning(f"User {user_id} didn't send a document")
            await update.message.reply_text("Пожалуйста, отправьте архив как документ")
            return WAITING_ARCHIVE

        file_name = update.message.document.file_name
        file_size = update.message.document.file_size

        # Проверка размера файла
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"User {user_id} sent file exceeding size limit: {file_size} bytes")
            await update.message.reply_text("❌ Размер файла превышает 20MB")
            return WAITING_ARCHIVE

        if not file_name.lower().endswith('.zip'):
            logger.warning(f"User {user_id} sent non-ZIP file: {file_name}")
            await update.message.reply_text("Пожалуйста, отправьте файл в формате ZIP")
            return WAITING_ARCHIVE

        # Скачиваем файл
        await update.message.reply_text("⏳ Начинаю обработку архива...")
        file = await update.message.document.get_file()

        # Создаем временный файл для архива
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            temp_zip_path = temp_file.name
            downloaded_bytes = await file.download_as_bytearray()
            temp_file.write(downloaded_bytes)

        # Создаем источник в БД
        source = context.bot_data['source_repo'].create_source_from_archive(
            filename=file_name,
            user_id=user_id
        )

        # Обрабатываем архив и получаем количество чанков
        chunks_count = await context.bot_data['archive_processor'].process_archive(temp_zip_path, source.id)

        # Обновляем статус источника
        context.bot_data['source_repo'].update_index_status(source.id, "completed")

        success_message = (
            f"✅ Архив успешно обработан и добавлен в базу знаний!\n"
            f"📊 Добавлено чанков: {chunks_count}\n"
            f"🗂 Источник: {file_name}"
        )

        await update.message.reply_text(success_message)
        logger.info(f"Successfully completed processing for user {user_id}, source {source.id}, chunks: {chunks_count}")

    except Exception as e:
        logger.error(f"Error processing archive for user {user_id}: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке архива. Пожалуйста, попробуйте позже."
        )
        if source:
            context.bot_data['source_repo'].update_index_status(source.id, "failed")

    finally:
        context.user_data.clear()

        if temp_zip_path and os.path.exists(temp_zip_path):
            try:
                os.unlink(temp_zip_path)
            except Exception as e:
                logger.error(f"Error removing temporary file {temp_zip_path}: {str(e)}")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена загрузки архива"""
    try:
        user_id = update.effective_user.id
        logger.info(f"User {user_id} cancelled archive upload")
        context.user_data.clear()
        await update.message.reply_text("Загрузка архива отменена.")
    except Exception as e:
        logger.error(f"Error in cancel handler: {e}", exc_info=True)
    return END


async def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик таймаута разговора"""
    try:
        context.user_data.clear()
        await update.message.reply_text(
            "⏰ Время ожидания истекло. Пожалуйста, начните заново с команды /add_rag_source"
        )
    except Exception as e:
        logger.error(f"Error in timeout handler: {e}", exc_info=True)
    return ConversationHandler.END


rag_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("add_rag_source", add_rag_source)],
    states={
        WAITING_ARCHIVE: [
            MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_archive),
            CommandHandler("cancel", cancel),
            CommandHandler("start", handle_other_commands),
            CommandHandler("help", handle_other_commands),
            CommandHandler("test", handle_other_commands),
            CommandHandler("qviz", handle_other_commands),
            CommandHandler("stop", handle_other_commands),
            CommandHandler("choose_rag", handle_other_commands),
            CommandHandler("add_rag_source", handle_other_commands),
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        MessageHandler(
            filters.ALL & ~filters.Document.ALL & ~filters.COMMAND,
            lambda u, c: u.message.reply_text("Пожалуйста, отправьте ZIP-архив или используйте /cancel")
        )
    ],
    conversation_timeout=300,
    name="rag_conversation",
    persistent=False,
    allow_reentry=True
)
