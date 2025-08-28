from telegram import Update
from telegram.ext import ContextTypes
from handlers.qviz import check_and_stop_dialog
from configs.config import config


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_and_stop_dialog(update, context)
    await update.message.reply_text(config.messages.HELP_MESSAGE)
