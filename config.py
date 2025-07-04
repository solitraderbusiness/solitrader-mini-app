"""
TG-Trade Suite Configuration
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Basic settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Database settings (we'll test these later)
    DATABASE_URL = os.getenv('DATABASE_URL', '')
    
    # API settings
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    
    # Basic validation
    @property
    def is_production(self) -> bool:
        return not self.DEBUG

# Create config instance
config = Config()
