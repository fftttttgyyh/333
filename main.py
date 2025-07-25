#!/usr/bin/env python3
"""
Telegram Bot for downloading videos and photos from multiple platforms
Supports: YouTube, TikTok, Instagram, Pinterest
"""

import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.handlers import BotHandlers
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main function to start the bot"""
    try:
        # Create application
        application = Application.builder().token(Config.BOT_TOKEN).build()
        
        # Initialize bot handlers
        bot_handlers = BotHandlers()
        
        # Add handlers
        application.add_handler(CommandHandler("start", bot_handlers.start_command))
        application.add_handler(CommandHandler("help", bot_handlers.help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handlers.handle_url))
        
        # Start the bot
        logger.info("Starting Telegram bot...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

if __name__ == "__main__":
    main()
