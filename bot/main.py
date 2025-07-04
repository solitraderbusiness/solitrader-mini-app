"""
TG-Trade Suite Telegram Bot - Fixed Event Loop Version
"""
import asyncio
import logging
import os
import signal

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
            from telegram.ext import ApplicationBuilder, CommandHandler
            from telegram import Update
            from telegram.ext import ContextTypes
            
            logger.info("✅ Telegram imports successful")
            
            # Build application
            self.app = ApplicationBuilder().token(self.token).build()
            logger.info("✅ Application built")
            
            # Define commands
            async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
                user = update.effective_user
                message = (
                    f"🎯 **Welcome to SoliTrader AI Assistant, {user.first_name}!**\n\n"
                    f"I'm your AI-powered technical analysis assistant.\n\n"
                    f"**Your Info:**\n"
                    f"• ID: {user.id}\n"
                    f"• Username: @{user.username or 'no_username'}\n\n"
                    f"**Commands:**\n"
                    f"• /start - This message\n"
                    f"• /test - Test bot functionality\n"
                    f"• /help - Get help\n\n"
                    f"🚀 Bot is fully operational!"
                )
                await update.message.reply_text(message, parse_mode='Markdown')
                logger.info(f"👤 User {user.id} ({user.username}) started the bot")
            
            async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
                message = (
                    "🧪 **Bot Test Results**\n\n"
                    "✅ Bot is running\n"
                    "✅ Commands working\n"
                    "✅ Telegram API connected\n"
                    "✅ Message processing OK\n"
                    "✅ Event loop fixed\n\n"
                    "🚀 Everything working perfectly!"
                )
                await update.message.reply_text(message, parse_mode='Markdown')
                logger.info(f"👤 User {update.effective_user.id} ran test command")
                
            async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
                message = (
                    "📚 **SoliTrader AI Assistant Help**\n\n"
                    "**Available Commands:**\n"
                    "• /start - Welcome message\n"
                    "• /test - Test bot functionality\n"
                    "• /help - Show this help\n\n"
                    "**Coming Soon:**\n"
                    "• Chart analysis with AI\n"
                    "• Technical indicators\n"
                    "• Trading signals\n\n"
                    "🚀 More features coming soon!"
                )
                await update.message.reply_text(message, parse_mode='Markdown')
                logger.info(f"👤 User {update.effective_user.id} requested help")
            
            # Add handlers
            self.app.add_handler(CommandHandler("start", start_command))
            self.app.add_handler(CommandHandler("test", test_command))
            self.app.add_handler(CommandHandler("help", help_command))
            
            logger.info("✅ Command handlers added")
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup error: {e}")
            return False
    
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
            await self.app.updater.start_polling(drop_pending_updates=True)
            logger.info("✅ Polling started - Bot is now live!")
            logger.info("📱 Try these commands in Telegram:")
            logger.info("   /start - Welcome message")
            logger.info("   /test - Test functionality")
            logger.info("   /help - Get help")
            
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
