import os
from dotenv import load_dotenv

def load_config():
    """Load configuration from environment variables"""
    load_dotenv()
    
    config = {
        'TOKEN': os.getenv('DISCORD_TOKEN'),
        'TARGET_BOT_ID': os.getenv('TARGET_BOT_ID'),
        'COMMAND_TIMEOUT': int(os.getenv('COMMAND_TIMEOUT', '30')),
        'DEFAULT_DELAY': float(os.getenv('DEFAULT_DELAY', '2.0')),
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    }
    
    # Validate required configuration
    if not config['TOKEN']:
        raise ValueError("DISCORD_TOKEN is required in .env file")
    
    if not config['TARGET_BOT_ID']:
        raise ValueError("TARGET_BOT_ID is required in .env file")
    
    return config
