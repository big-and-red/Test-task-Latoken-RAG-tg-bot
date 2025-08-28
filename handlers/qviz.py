# handlers/qviz.py
import logging

from anthropic import Anthropic
from telegram import Update
from telegram.ext import ContextTypes
from services.search_service import SearchService
from db.connection import get_db
from dotenv import load_dotenv


import asyncio
load_dotenv()
logger = logging.getLogger(__name__)

client = Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY',)


async def get_claude_response(user_query: str, context: str) -> str:
    try:
        response = await asyncio.to_thread(
            lambda: client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=3000,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": f"Context: {context}\n\nQuestion: {user_query}\n\nPlease answer based only on the provided context. Please answer only on russian language."
                    }
                ]
            )
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Error getting Claude response: {e}", exc_info=True)
        return "Извините, произошла ошибка при получении ответа. Попробуйте позже."


async def check_and_stop_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет и останавливает диалог если он активен"""
    if context.user_data.get('is_dialog_active'):
        context.user_data['is_dialog_active'] = False
        await update.message.reply_text(
            "🔴 Режим диалога деактивирован из-за использования команды.\n"
            "Для начала нового диалога используйте /qviz"
        )
        return True
    return False


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /qviz"""
    user_id = update.effective_user.id

    # Проверяем наличие активного источника
    active_rag_repo = context.bot_data['active_rag_repo']
    active_source = active_rag_repo.get_active_source(user_id)

    if not active_source:
        await update.message.reply_text(
            "❌ У вас не выбран RAG источник.\n"
            "Пожалуйста, выберите источник командой /choose_rag"
        )
        return

    # Устанавливаем флаг активного диалога
    context.user_data['is_dialog_active'] = True
    context.user_data['active_source_id'] = active_source.id

    await update.message.reply_text(
        f"🟢 Режим диалога активирован!\n\n"
        f"Текущий RAG источник: {active_source.name}\n"
        "Задавайте любые вопросы.\n"
        "Для выхода используйте любую команду или /stop"
    )


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stop"""
    if context.user_data.get('is_dialog_active'):
        context.user_data['is_dialog_active'] = False
        await update.message.reply_text(
            "🔴 Режим диалога деактивирован.\n"
            "Для начала нового диалога используйте /qviz"
        )
    else:
        await update.message.reply_text(
            "❗️ Режим диалога не был активирован.\n"
            "Используйте /qviz для начала диалога"
        )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех текстовых сообщений в режиме диалога"""
    if context.user_data.get('is_dialog_active'):
        user_message = update.message.text
        active_source_id = context.user_data.get('active_source_id')

        try:
            # Получаем сессию через генератор
            db = next(get_db())
            search_service = SearchService(db)

            # Показываем пользователю, что запрос обрабатывается
            waiting_message = await update.message.reply_text("⏳ Ищу информацию и формирую ответ...")

            # Ищем похожие тексты
            similar_texts = await search_service.search(
                source_id=active_source_id,
                query=user_message,
            )

            if not similar_texts:
                await waiting_message.delete()
                await update.message.reply_text(
                    "❌ К сожалению, не удалось найти релевантных фрагментов по вашему запросу."
                )
                return

            # Формируем контекст из найденных текстов
            context_text = "\n".join(similar_texts)

            gpt_response = await get_claude_response(user_message, context_text)

            await waiting_message.delete()

            # Формируем и отправляем ответ
            response = (
                f"🤖 Ответ:\n{gpt_response}\n\n"
                f"📚 Исходные фрагменты:\n"
            )

            # Добавляем исходные фрагменты
            for i, text in enumerate(similar_texts, 1):
                response += f"{i}. {text}\n\n"

            # Отправляем ответ частями, если он слишком длинный
            if len(response) > 4096:
                # Сначала отправляем ответ GPT
                await update.message.reply_text(f"🤖 Ответ:\n{gpt_response}")

                # Затем отправляем исходные фрагменты
                fragments_response = "📚 Исходные фрагменты:\n"
                for i, text in enumerate(similar_texts, 1):
                    fragments_response += f"{i}. {text}\n\n"

                    # Отправляем каждые 4000 символов
                    if len(fragments_response) > 4000:
                        await update.message.reply_text(fragments_response)
                        fragments_response = ""

                # Отправляем оставшиеся фрагменты
                if fragments_response:
                    await update.message.reply_text(fragments_response)
            else:
                await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Error during search and response generation: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже."
            )
        finally:
            if 'db' in locals():
                db.close()
