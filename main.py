import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
from pathlib import Path

from jarvis_engine import JarvisEngine
from file_manager import FileManager
from error_handler import ErrorHandler

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/jarvis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JarvisBot:
    def __init__(self):
        self.token = os.getenv('BOT_TOKEN')
        self.owner_id = int(os.getenv('OWNER_ID', 0))
        self.webapp_url = os.getenv('WEBAPP_URL', 'https://your-domain.com')
        
        self.file_manager = FileManager()
        self.jarvis_engine = JarvisEngine()
        self.error_handler = ErrorHandler()
        
        # Load settings
        self.settings = self.load_settings()
        
        # Initialize application
        self.app = Application.builder().token(self.token).build()
        self.setup_handlers()

    def load_settings(self):
        try:
            with open('config/settings.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            default_settings = {
                "devs": [self.owner_id],
                "access_mode": "dev",
                "memory": {},
                "enabled_plugins": []
            }
            os.makedirs('config', exist_ok=True)
            with open('config/settings.json', 'w') as f:
                json.dump(default_settings, f, indent=2)
            return default_settings

    def save_settings(self):
        with open('config/settings.json', 'w') as f:
            json.dump(self.settings, f, indent=2)

    def is_authorized(self, user_id):
        if self.settings['access_mode'] == 'public':
            return True
        return user_id in self.settings['devs'] or user_id == self.owner_id

    def setup_handlers(self):
        # Core commands
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("info", self.info_command))
        self.app.add_handler(CommandHandler("webapp", self.webapp_command))
        self.app.add_handler(CommandHandler("tree", self.tree_command))
        self.app.add_handler(CommandHandler("memory", self.memory_command))
        self.app.add_handler(CommandHandler("undo", self.undo_command))
        self.app.add_handler(CommandHandler("log", self.log_command))
        self.app.add_handler(CommandHandler("adddev", self.adddev_command))
        self.app.add_handler(CommandHandler("enable", self.enable_command))
        self.app.add_handler(CommandHandler("disable", self.disable_command))
        
        # File and document handlers
        self.app.add_handler(MessageHandler(filters.Document, self.handle_document))
        
        # Natural language handler
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Load dynamic feature handlers
        self.load_feature_handlers()

    def load_feature_handlers(self):
        """Dynamically load handlers from features directory"""
        features_dir = Path('features')
        if not features_dir.exists():
            return
            
        for feature_dir in features_dir.iterdir():
            if feature_dir.is_dir() and (feature_dir / 'handler.py').exists():
                try:
                    # Dynamic import and handler registration would go here
                    # This is a simplified version
                    pass
                except Exception as e:
                    logger.error(f"Failed to load feature {feature_dir.name}: {e}")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [[InlineKeyboardButton("Open WebApp", web_app=WebAppInfo(url=f"{self.webapp_url}/miniapp"))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤖 JARVIS v2 - AI Assistant\n\nUse /help for commands or open WebApp.",
            reply_markup=reply_markup
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
🔧 Commands:
/start - Bot info
/help - This help
/info - System stats
/webapp - Open interface
/tree - File structure
/memory <key> <val> - Save data
/undo - Restore backup
        """
        await update.message.reply_text(help_text)

    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        features_count = len(list(Path('features').iterdir())) if Path('features').exists() else 0
        info_text = f"""
📊 System Info:
Features: {features_count}
Mode: {self.settings['access_mode']}
Devs: {len(self.settings['devs'])}
        """
        await update.message.reply_text(info_text)

    async def webapp_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [[InlineKeyboardButton("Launch WebApp", web_app=WebAppInfo(url=f"{self.webapp_url}/miniapp"))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🌐 WebApp Interface:", reply_markup=reply_markup)

    async def tree_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
            
        tree = self.file_manager.get_file_tree()
        await update.message.reply_text(f"```\n{tree}\n```", parse_mode='Markdown')

    async def memory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
            
        if len(context.args) >= 2:
            key, value = context.args[0], ' '.join(context.args[1:])
            self.settings['memory'][key] = value
            self.save_settings()
            await update.message.reply_text(f"💾 Saved: {key}")
        else:
            memory_items = list(self.settings['memory'].keys())
            await update.message.reply_text(f"🧠 Memory: {', '.join(memory_items)}")

    async def undo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
            
        success = self.file_manager.restore_backup()
        if success:
            await update.message.reply_text("↩️ Restored from backup")
        else:
            await update.message.reply_text("❌ No backup found")

    async def log_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
            
        try:
            with open('logs/jarvis.log', 'r') as f:
                logs = f.readlines()[-10:]  # Last 10 lines
                log_text = ''.join(logs)
                await update.message.reply_text(f"```\n{log_text}\n```", parse_mode='Markdown')
        except FileNotFoundError:
            await update.message.reply_text("📝 No logs found")

    async def adddev_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != self.owner_id:
            await update.message.reply_text("❌ Owner only")
            return
            
        if context.args:
            user_id = int(context.args[0])
            if user_id not in self.settings['devs']:
                self.settings['devs'].append(user_id)
                self.save_settings()
                await update.message.reply_text(f"✅ Added dev: {user_id}")
            else:
                await update.message.reply_text("❌ Already a dev")

    async def enable_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
            
        if context.args:
            plugin = context.args[0]
            if plugin not in self.settings['enabled_plugins']:
                self.settings['enabled_plugins'].append(plugin)
                self.save_settings()
                await update.message.reply_text(f"🔌 Enabled: {plugin}")

    async def disable_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
            
        if context.args:
            plugin = context.args[0]
            if plugin in self.settings['enabled_plugins']:
                self.settings['enabled_plugins'].remove(plugin)
                self.save_settings()
                await update.message.reply_text(f"🚫 Disabled: {plugin}")

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
            
        document = update.message.document
        caption = update.message.caption or ""
        
        # Download file
        file_path = f"uploads/{document.file_name}"
        os.makedirs('uploads', exist_ok=True)
        
        file = await context.bot.get_file(document.file_id)
        await file.download_to_drive(file_path)
        
        # Process with AI
        if document.file_name.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            prompt = f"File: {document.file_name}\nContent: {content}\nCaption: {caption}"
            response = await self.jarvis_engine.process_prompt(prompt, update.effective_user.id)
            await update.message.reply_text(response)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Check if it's a DM or group mention
        if update.message.chat.type == 'private':
            should_respond = True
        else:
            message_text = update.message.text.lower()
            should_respond = 'jarvis' in message_text or f'@{context.bot.username}' in message_text
        
        if should_respond and self.is_authorized(update.effective_user.id):
            response = await self.jarvis_engine.process_prompt(
                update.message.text, 
                update.effective_user.id
            )
            await update.message.reply_text(response)

    def run(self):
        logger.info("Starting JARVIS v2...")
        self.app.run_polling()