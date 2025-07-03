import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello from tg-trade-suite!")

async def main() -> None:
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN not set")
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    logger.info("Bot started")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
