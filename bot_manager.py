# bot_manager.py - Updated with all required imports
import asyncio
import time
import logging
import signal
import sys
import os  # ADD THIS IMPORT
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    FloodWaitError,
    RPCError
)
from telethon.tl.types import MessageEntityMention

from config import Config

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

class AutoResponderBot:
    def __init__(self):
        self.client = None
        self.me = None
        self.is_running = False
        self.restart_count = 0
        self.last_restart_time = 0
        
        # Rate limiting
        self.chat_cooldowns = {}
        self.user_cooldowns = {}
        
        # Health monitoring
        self.last_health_check = time.time()
        self.messages_processed = 0
        self.messages_responded = 0
        
    def is_on_cooldown(self, chat_id, user_id):
        """Check if we should respond based on cooldowns"""
        now = time.time()
        
        # Check chat cooldown
        if chat_id in self.chat_cooldowns:
            if now - self.chat_cooldowns[chat_id] < Config.COOLDOWN_PER_CHAT:
                return True
        
        # Check user cooldown
        if user_id in self.user_cooldowns:
            if now - self.user_cooldowns[user_id] < Config.COOLDOWN_PER_USER:
                return True
        
        return False
    
    def update_cooldowns(self, chat_id, user_id):
        """Update cooldown timestamps"""
        now = time.time()
        self.chat_cooldowns[chat_id] = now
        self.user_cooldowns[user_id] = now
        
        # Clean old cooldowns (optional, to prevent memory leak)
        self._clean_old_cooldowns()
    
    def _clean_old_cooldowns(self):
        """Remove old cooldown entries"""
        now = time.time()
        max_age = max(Config.COOLDOWN_PER_CHAT, Config.COOLDOWN_PER_USER) * 2
        
        self.chat_cooldowns = {
            k: v for k, v in self.chat_cooldowns.items() 
            if now - v < max_age
        }
        self.user_cooldowns = {
            k: v for k, v in self.user_cooldowns.items() 
            if now - v < max_age
        }
    
    async def initialize_client(self):
        """Initialize Telegram client"""
        try:
            logger.info("Initializing Telegram client...")
            
            # Create client
            self.client = TelegramClient(
                Config.SESSION_NAME,
                Config.API_ID,
                API_HASH=Config.API_HASH,
                device_model="AutoResponderBot",
                system_version="24/7",
                app_version="1.0.0",
                lang_code="en",
                system_lang_code="en-US"
            )
            
            # Add event handlers
            self.client.add_event_handler(
                self.handle_message,
                events.NewMessage(incoming=True)
            )
            
            # Connect and authenticate
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                logger.info("Sending code request...")
                await self.client.send_code_request(Config.PHONE_NUMBER)
                
                # Get code from environment or user input
                # On Railway, we need to use environment variable
                code = os.getenv("TELEGRAM_CODE", "")
                if not code:
                    # In Railway, we can't use input(), so we'll log and exit
                    logger.error("TELEGRAM_CODE environment variable not set!")
                    logger.error("Please set TELEGRAM_CODE in Railway variables with the verification code.")
                    logger.error("For first run, you need to:")
                    logger.error("1. Check Railway logs for the code request")
                    logger.error("2. Get the code from Telegram")
                    logger.error("3. Set TELEGRAM_CODE in environment variables")
                    logger.error("4. Redeploy the app")
                    return False
                
                try:
                    await self.client.sign_in(Config.PHONE_NUMBER, code)
                except SessionPasswordNeededError:
                    password = os.getenv("TELEGRAM_PASSWORD", "")
                    if not password:
                        logger.error("TELEGRAM_PASSWORD environment variable not set for 2FA!")
                        return False
                    await self.client.sign_in(password=password)
                except Exception as e:
                    logger.error(f"Failed to sign in with code: {str(e)}")
                    return False
            else:
                logger.info("Already authorized, logging in...")
            
            # Get user info
            self.me = await self.client.get_me()
            logger.info(f"Logged in as: {self.me.first_name} (@{self.me.username})")
            
            # Start the client
            self.is_running = True
            logger.info("Client initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize client: {str(e)}")
            await self.safe_disconnect()
            return False
    
    async def safe_disconnect(self):
        """Safely disconnect client"""
        if self.client and self.client.is_connected():
            await self.client.disconnect()
        self.client = None
        self.is_running = False
    
    async def handle_message(self, event):
        """Handle incoming messages"""
        try:
            self.messages_processed += 1
            
            # Don't respond to our own messages
            if event.sender_id == self.me.id:
                return
            
            # Get chat info
            chat = await event.get_chat()
            sender = await event.get_sender()
            
            # Skip if blacklisted
            if sender.id in Config.BLACKLIST:
                return
            
            # Check whitelist if set
            if Config.WHITELIST and sender.id not in Config.WHITELIST:
                return
            
            # Check allowed chats if set
            if Config.ALLOWED_CHATS and chat.id not in Config.ALLOWED_CHATS:
                return
            
            # Determine if we should respond
            should_respond = False
            response_type = None
            
            # 1. Direct Message
            if "dm" in Config.RESPOND_TO and event.is_private:
                should_respond = True
                response_type = "DM"
            
            # 2. Mention by username
            elif "mention" in Config.RESPOND_TO and event.message.message:
                message_text = event.message.message.lower()
                if self.me.username and f"@{self.me.username.lower()}" in message_text:
                    should_respond = True
                    response_type = "mention"
            
            # 3. Reply to our message
            elif "reply" in Config.RESPOND_TO and event.is_reply:
                try:
                    replied_msg = await event.get_reply_message()
                    if replied_msg.sender_id == self.me.id:
                        should_respond = True
                        response_type = "reply"
                except:
                    pass
            
            if should_respond:
                # Check cooldown
                if self.is_on_cooldown(chat.id, sender.id):
                    logger.info(f"Cooldown active for chat {chat.id}, user {sender.id}")
                    return
                
                # Update cooldowns
                self.update_cooldowns(chat.id, sender.id)
                
                # Prepare response
                username = sender.first_name or sender.username or "User"
                response_text = Config.RESPONSE_TEMPLATE.format(username=username)
                
                # Show typing action
                async with self.client.action(chat.id, 'typing'):
                    await asyncio.sleep(1)  # Typing delay
                
                # Send response
                await event.reply(response_text)
                
                self.messages_responded += 1
                logger.info(f"Responded to {username} ({response_type}) in chat {chat.id}")
        
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
    
    async def health_check(self):
        """Perform health check"""
        try:
            if not self.is_running or not self.client:
                return False
            
            # Check connection
            if not await self.client.is_user_authorized():
                logger.warning("Health check: Not authorized")
                return False
            
            # Try to get our own info
            me = await self.client.get_me()
            if not me:
                logger.warning("Health check: Cannot get user info")
                return False
            
            self.last_health_check = time.time()
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
    
    async def run(self):
        """Main run loop with auto-restart"""
        while True:
            try:
                logger.info(f"Starting bot (attempt {self.restart_count + 1}/{Config.MAX_RESTART_ATTEMPTS})")
                
                # Initialize client
                if await self.initialize_client():
                    logger.info("Bot started successfully")
                    
                    # Reset restart counter on successful start
                    self.restart_count = 0
                    
                    # Run until disconnected
                    await self.client.run_until_disconnected()
                    
                    logger.warning("Client disconnected")
                else:
                    logger.error("Failed to initialize client")
                
                # Increment restart counter
                self.restart_count += 1
                
                # Check if we've exceeded max restarts
                if self.restart_count >= Config.MAX_RESTART_ATTEMPTS:
                    logger.error(f"Exceeded maximum restart attempts ({Config.MAX_RESTART_ATTEMPTS})")
                    break
                
                # Wait before restarting
                logger.info(f"Waiting {Config.AUTO_RESTART_DELAY} seconds before restart...")
                await asyncio.sleep(Config.AUTO_RESTART_DELAY)
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {str(e)}")
                await asyncio.sleep(Config.AUTO_RESTART_DELAY)
        
        # Clean shutdown
        await self.safe_disconnect()
        logger.info("Bot shutdown complete")
    
    def get_stats(self):
        """Get bot statistics"""
        return {
            "running": self.is_running,
            "restart_count": self.restart_count,
            "messages_processed": self.messages_processed,
            "messages_responded": self.messages_responded,
            "last_health_check": datetime.fromtimestamp(self.last_health_check).isoformat() if self.last_health_check else None
        }
