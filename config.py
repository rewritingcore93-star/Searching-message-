# config.py
import os
import json
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram API Credentials
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    PHONE_NUMBER = os.getenv("PHONE_NUMBER", "")
    SESSION_NAME = os.getenv("SESSION_NAME", "my_account")
    
    # Bot Settings
    AUTO_RESTART_DELAY = int(os.getenv("AUTO_RESTART_DELAY", 10))
    MAX_RESTART_ATTEMPTS = int(os.getenv("MAX_RESTART_ATTEMPTS", 10))
    HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", 300))
    
    # Response Settings
    RESPONSE_TEMPLATE = os.getenv(
        "RESPONSE_TEMPLATE",
        "Good question, Where is Domain?? Maybe still searching msti 🔎 , It will take time for him to reach again here ... sorry for late response, I will let him know that {username} is still with you .Thank you for Waiting .."
    )
    
    # Cooldown Settings (in seconds)
    COOLDOWN_PER_CHAT = int(os.getenv("COOLDOWN_PER_CHAT", 60))
    COOLDOWN_PER_USER = int(os.getenv("COOLDOWN_PER_USER", 300))
    
    # Monitoring
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    SENTRY_DSN = os.getenv("SENTRY_DSN", "")
    
    # Whitelist/Blacklist (JSON strings)
    WHITELIST = json.loads(os.getenv("WHITELIST", "[]"))
    BLACKLIST = json.loads(os.getenv("BLACKLIST", "[]"))
    
    # Allowed chats (empty means all)
    ALLOWED_CHATS = json.loads(os.getenv("ALLOWED_CHATS", "[]"))
    
    # Response types (comma separated)
    RESPOND_TO = os.getenv("RESPOND_TO", "dm,mention,reply").split(",")
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.API_ID:
            raise ValueError("API_ID is required")
        if not cls.API_HASH:
            raise ValueError("API_HASH is required")
        if not cls.PHONE_NUMBER:
            raise ValueError("PHONE_NUMBER is required")
        
        # Convert IDs to integers
        cls.WHITELIST = [int(id) for id in cls.WHITELIST if id]
        cls.BLACKLIST = [int(id) for id in cls.BLACKLIST if id]
        cls.ALLOWED_CHATS = [int(id) for id in cls.ALLOWED_CHATS if id]
        
        return True
