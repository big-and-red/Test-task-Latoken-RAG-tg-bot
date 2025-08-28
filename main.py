# main.py

from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from configs.config import config
from db.connection import get_db
from handlers import start, help, test, qviz, add_rag_source, choose_rag
from services.rag_service import RagArchiveProcessor
from services.text_service import TextService
from services.temp_file_service import TempFilesService
from db.repos.embedding_repo import EmbeddingRepo
from db.repos.rag_source_repo import RagSourceRepo
from db.repos.active_rag_repo import ActiveRagSourceRepo


def main():
    # Создание зависимостей
    db = next(get_db())
    source_repo = RagSourceRepo(db)
    embedding_repo = EmbeddingRepo(db)
    active_rag_repo = ActiveRagSourceRepo(db)
    text_service = TextService()
    temp_files = TempFilesService()

    archive_processor = RagArchiveProcessor(
        source_repo=source_repo,
        embedding_repo=embedding_repo,
        text_service=text_service,
        temp_files=temp_files,
        model_name_or_path="sentence-transformers/distiluse-base-multilingual-cased-v1",
    )

    application = Application.builder().token(config.TELEGRAM_TOKEN).build()

    application.bot_data.update({
        'archive_processor': archive_processor,
        'source_repo': source_repo,
        'active_rag_repo': active_rag_repo,
    })

    application.add_handler(add_rag_source.rag_conv_handler)

    # Затем остальные обработчики
    application.add_handler(CommandHandler("start", start.start_command))
    application.add_handler(CommandHandler("help", help.help_command))
    application.add_handler(CommandHandler("test", test.test_command))
    application.add_handler(CommandHandler("qviz", qviz.quiz_command))
    application.add_handler(CommandHandler("stop", qviz.stop_command))
    application.add_handler(CommandHandler("choose_rag", choose_rag.choose_rag_command))

    application.add_handler(CallbackQueryHandler(choose_rag.choose_rag_callback, pattern="^choose_rag_"))
    application.add_handler(CallbackQueryHandler(test.button_handler, pattern="^test_"))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, qviz.message_handler))

    print('Starting bot...')
    application.run_polling()


if __name__ == '__main__':
    main()