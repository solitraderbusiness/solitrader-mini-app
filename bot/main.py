"""
TG-Trade Suite Telegram Bot - Enhanced with Chart Analysis
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal



from telegram import Update                 # make the names available now
from telegram.ext import (
    ContextTypes,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

# (optional) if you prefer everything at top level:
# from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters


logging.getLogger("telegram.ext").setLevel(logging.DEBUG)   # ▶ ADD THIS



# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.app = None
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        
    async def setup(self):
        """Setup the bot"""
        logger.info("🚀 Setting up Telegram bot...")
        
        if not self.token:
            logger.error("❌ No token found!")
            return False
            
        logger.info(f"🔑 Token: {self.token[:20]}...")
        
        try:

            
            logger.info("✅ Telegram imports successful")
            
            # Build application
            self.app = ApplicationBuilder().token(self.token).build()
            logger.info("✅ Application built")
            
            # Define commands
            async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
                user = update.effective_user
                message = (
                    f"🎯 **Welcome to SoliTrader Chart Analyzer, {user.first_name}!**\n\n"
                    f"I'm your AI-powered technical analysis assistant.\n\n"
                    f"**Your Info:**\n"
                    f"• ID: {user.id}\n"
                    f"• Username: @{user.username or 'no_username'}\n\n"
                    f"**How to use:**\n"
                    f"1️⃣ Send me any trading chart image\n"
                    f"2️⃣ I'll analyze it with AI\n"
                    f"3️⃣ Get detailed technical analysis\n\n"
                    f"**Commands:**\n"
                    f"• /start - This message\n"
                    f"• /analyze - Instructions for analysis\n"
                    f"• /help - Get help\n\n"
                    f"📊 Just send me a chart image to start!"
                )
                await update.message.reply_text(message, parse_mode='Markdown')
                logger.info(f"👤 User {user.id} ({user.username}) started the bot")
            
            async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
                message = (
                    "📊 **How to Analyze Charts**\n\n"
                    "Simply send me a chart image and I'll analyze it!\n\n"
                    "**Supported formats:** PNG, JPG, JPEG\n"
                    "**Max size:** 5MB\n\n"
                    "**What I analyze:**\n"
                    "• 📈 Trend direction\n"
                    "• 🎯 Support/Resistance levels\n"
                    "• 📐 Chart patterns\n"
                    "• 📊 Volume (if visible)\n"
                    "• 🎪 Price targets\n"
                    "• ⚠️ Risk assessment\n\n"
                    "Send me a chart image now!"
                )
                await update.message.reply_text(message, parse_mode='Markdown')
                logger.info(f"👤 User {update.effective_user.id} requested analyze info")
                
            async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
                message = (
                    "📚 **SoliTrader AI Assistant Help**\n\n"
                    "**Available Commands:**\n"
                    "• /start - Welcome message\n"
                    "• /analyze - How to analyze charts\n"
                    "• /help - Show this help\n\n"
                    "**To analyze a chart:**\n"
                    "Just send me any trading chart image!\n\n"
                    "**Supported formats:** PNG, JPG, JPEG (max 5MB)\n\n"
                    "⚠️ *Analysis is for educational purposes only*"
                )
                await update.message.reply_text(message, parse_mode='Markdown')
                logger.info(f"👤 User {update.effective_user.id} requested help")
            
            # Add handlers
            self.app.add_handler(CommandHandler("start", start_command))
            self.app.add_handler(CommandHandler("analyze", analyze_command))
            self.app.add_handler(CommandHandler("help", help_command))
            
            # Add image handler
            self.app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, self._handle_image))
            
            logger.info("✅ All handlers added")
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup error: {e}")
            return False
    
   

   # >>> replace the whole _handle_image in TelegramBot with this one
    async def _handle_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Receive a chart image (photo **or** image-document), download it,
        validate it, run GPT-4 Vision analysis, and reply to the user.
        """
        try:
            user = update.effective_user
            message = update.message

            # ── pick the best available Telegram file object ───────────
            tg_file_obj = None
            file_ext = "jpg"                     # default if we can’t detect

            if message.photo:
                # Image sent as a regular photo → take the largest size
                tg_file_obj = message.photo[-1]
                file_ext = "jpg"
            elif (
                message.document
                and message.document.mime_type
                and message.document.mime_type.startswith("image/")
            ):
                # Image sent/forwarded as a document
                tg_file_obj = message.document
                # Try to guess the extension from the filename
                if tg_file_obj.file_name:
                    file_ext = os.path.splitext(tg_file_obj.file_name)[1].lstrip(".") or "jpg"
            else:
                await message.reply_text(
                    "❌ **No image found**\n\n"
                    "Please send a chart screenshot as a photo or attach it as an image file.",
                    parse_mode="Markdown",
                )
                return
            # ──────────────────────────────────────────────────────────

            # Size sanity-check (5 MB hard limit)
            max_bytes = 5 * 1024 * 1024
            if tg_file_obj.file_size and tg_file_obj.file_size > max_bytes:
                await message.reply_text(
                    f"❌ **Image too large!**\n\n"
                    f"Your image: {tg_file_obj.file_size / 1024 / 1024:.1f} MB\n"
                    f"Maximum size: 5.0 MB",
                    parse_mode="Markdown",
                )
                return

            # Send a “processing” placeholder
            processing_msg = await message.reply_text(
                "📊 **Image received!**\n\n"
                "🤖 AI is analyzing your chart…\n"
                "⏱️ Usually takes 10-30 seconds.",
                parse_mode="Markdown",
            )

            # Import helpers (keeps top-level imports minimal inside Docker)
            import sys

            sys.path.append("/app")
            from utils.image_handler import image_handler
            from utils.ai_analyzer import ai_analyzer

            # Download the file from Telegram
            telegram_file = await context.bot.get_file(tg_file_obj.file_id)
            file_path = await image_handler.download_telegram_image(telegram_file, file_ext)

            if not file_path:
                await processing_msg.edit_text(
                    "❌ **Download failed**\n\nCould not retrieve your image. Please try again.",
                    parse_mode="Markdown",
                )
                return

            # Validate / normalise the image
            is_valid, validation_message = await image_handler.validate_and_process_image(file_path)
            if not is_valid:
                await processing_msg.edit_text(
                    f"❌ **Invalid image**\n\n{validation_message}\n\n"
                    f"Please send a clear chart screenshot (PNG/JPG, ≤ 5 MB).",
                    parse_mode="Markdown",
                )
                return

            # Run GPT-4o Vision analysis
            analysis_result = await ai_analyzer.analyze_chart(file_path, user.id)

            # Format and send the answer
            analysis_text = ai_analyzer.format_analysis_message(analysis_result)
            await processing_msg.edit_text(analysis_text, parse_mode="Markdown")

            logger.info(
                "📊 Chart analysis completed for user %s – success=%s",
                user.id,
                analysis_result.get("success", False),
            )

        except ImportError as e:
            logger.error("❌ Import error: %s", e, exc_info=True)
            await message.reply_text(
                "❌ **System error**\n\nAnalysis modules not available. Please contact support.",
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error("❌ Error handling image: %s", e, exc_info=True)
            await message.reply_text(
                "❌ **Unexpected error**\n\nCould not process your image. Please try again.",
                parse_mode="Markdown",
            )
# <<< end of replacement




    async def start(self):
        """Start the bot"""
        logger.info("🔄 Starting bot...")
        
        try:
            # Initialize the application
            await self.app.initialize()
            logger.info("✅ Bot initialized")
            
            # Start the application
            await self.app.start()
            logger.info("✅ Bot started")
            
            # Start polling
            await self.app.updater.start_polling()
            logger.info("✅ Polling started - Bot is now live!")
            logger.info("📱 Bot ready to analyze charts!")
            logger.info("   Send any trading chart image to get AI analysis")
            
            # Keep running
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Start error: {e}")
            raise
    
    async def stop(self):
        """Stop the bot gracefully"""
        if self.app:
            try:
                logger.info("🛑 Stopping bot...")
                await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()
                logger.info("✅ Bot stopped gracefully")
            except Exception as e:
                logger.error(f"Error stopping bot: {e}")

async def main():
    """Main entry point"""
    logger.info("🎯 TG-Trade Suite Bot Starting...")
    logger.info("=" * 50)
    
    bot = TelegramBot()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler():
        logger.info("🛑 Received shutdown signal")
        raise KeyboardInterrupt
    
    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    for sig in [signal.SIGTERM, signal.SIGINT]:
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        # Setup bot
        if not await bot.setup():
            logger.error("❌ Bot setup failed")
            return
            
        # Start bot
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by signal")
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.stop()
        logger.info("🏁 Bot shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
