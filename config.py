"""
TG-Trade Suite Configuration
"""
import os
from typing import Optional
from pydantic import BaseSettings, validator
from dotenv import load_dotenv

load_dotenv()

class Config(BaseSettings):
    """Application configuration"""
    
    # Telegram Bot Settings
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_URL: Optional[str] = None
    
    # Database Settings
    DATABASE_URL: str
    
    # OpenAI Settings
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TEMPERATURE: float = 0.1
    
    # Payment Settings - TON (placeholder)
    TON_WALLET_ADDRESS: Optional[str] = None
    TON_PRIVATE_KEY: Optional[str] = None
    TON_NETWORK: str = "testnet"
    TON_API_KEY: Optional[str] = None
    
    # Payment Settings - Tether (placeholder)
    TETHER_WALLET_ADDRESS: Optional[str] = None
    TETHER_PRIVATE_KEY: Optional[str] = None
    ETHEREUM_RPC_URL: Optional[str] = None
    TETHER_CONTRACT_ADDRESS: str = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
    
    # Application Settings
    APP_URL: str = "https://your-domain.com"
    DEBUG: bool = False
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    
    # File Storage Settings
    UPLOAD_FOLDER: str = "/app/uploads"
    MAX_FILE_SIZE: int = 5242880  # 5MB
    IMAGE_RETENTION_SECONDS: int = 60
    IMAGE_CLEANUP_ENABLED: bool = True
    ALLOWED_EXTENSIONS: set = {"png", "jpg", "jpeg"}
    
    # Redis Settings
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Rate Limiting Settings
    DAILY_FREE_ANALYSES: int = 3
    ANALYSIS_PACKAGE_SIZE: int = 10
    ANALYSIS_PACKAGE_PRICE_USD: float = 5.00
    
    # Monitoring Settings
    LOG_LEVEL: str = "INFO"
    
    @validator('TELEGRAM_BOT_TOKEN')
    def validate_telegram_token(cls, v):
        if not v or v == "YOUR_BOT_TOKEN_FROM_BOTFATHER":
            raise ValueError('TELEGRAM_BOT_TOKEN is required - get it from @BotFather')
        return v
    
    @validator('OPENAI_API_KEY')
    def validate_openai_key(cls, v):
        if not v or v == "YOUR_OPENAI_API_KEY_HERE":
            raise ValueError('OPENAI_API_KEY is required - get it from OpenAI')
        return v
    
    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        if not v:
            raise ValueError('DATABASE_URL is required')
        return v
    
    @property
    def is_production(self) -> bool:
        return not self.DEBUG
    
    @property
    def webhook_enabled(self) -> bool:
        return bool(self.TELEGRAM_WEBHOOK_URL)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Chart Analysis Prompt Template
CHART_ANALYSIS_PROMPT = """
You are an expert technical analyst with years of experience in financial markets. 
Analyze this trading chart image and provide a comprehensive technical analysis.

Look for and analyze:
1. TREND DIRECTION: Identify the overall trend (uptrend, downtrend, or sideways)
2. SUPPORT & RESISTANCE: Identify key price levels where price has bounced or been rejected
3. CHART PATTERNS: Look for classic patterns like triangles, flags, head & shoulders, double tops/bottoms, etc.
4. VOLUME ANALYSIS: If volume is visible, analyze volume patterns and confirmations
5. INDICATORS: If technical indicators are visible, interpret their signals
6. KEY INSIGHTS: Identify the most important observations about this chart

Provide specific price levels when they are clearly visible on the chart.
Be objective and base your analysis only on what you can see in the chart.
Consider the timeframe if it's visible.

Format your response as a JSON object with this exact structure:
{
  "trend": "uptrend/downtrend/sideways",
  "confidence": 0.85,
  "support_levels": [1234.56, 1220.30],
  "resistance_levels": [1250.00, 1275.80],
  "patterns": ["ascending triangle", "bullish flag"],
  "volume_analysis": "Volume analysis description or null if not visible",
  "indicators": "Technical indicators analysis or null if not visible",
  "key_insights": "Most important observations about this chart",
  "risk_level": "low/medium/high",
  "timeframe_detected": "1m/5m/15m/1h/4h/1d/1w/1M or null if not visible",
  "market_bias": "bullish/bearish/neutral",
  "price_targets": [1300.00, 1350.00],
  "stop_loss_level": 1200.00,
  "summary": "2-3 sentence summary suitable for sharing"
}

Only include price levels that are clearly visible on the chart. 
If certain information is not visible or unclear, use null for those fields.
Be conservative in your confidence score - only use high confidence (0.8+) when patterns are very clear.
"""

# Error Messages
ERROR_MESSAGES = {
    'rate_limit_exceeded': '⚠️ Rate limit exceeded. Please wait before trying again.',
    'invalid_image': '❌ Invalid image format. Please send a PNG, JPG, or JPEG file.',
    'image_too_large': '❌ Image is too large. Maximum size is 5MB.',
    'analysis_failed': '❌ Analysis failed. Please try again with a different image.',
    'daily_limit_reached': '🚫 Daily analysis limit reached. Upgrade to continue analyzing charts.',
    'network_error': '🌐 Network error. Please check your connection and try again.',
    'unknown_error': '❌ An unexpected error occurred. Please try again later.'
}

# Success Messages
SUCCESS_MESSAGES = {
    'analysis_complete': '✅ Analysis complete! Here are the results:',
    'image_received': '📊 Image received. Analyzing chart...',
    'analysis_shared': '🔗 Analysis shared successfully!'
}

# UI Text
UI_TEXT = {
    'welcome_message': """
🎯 **Welcome to SoliTrader Chart Analyzer!**

I'm your AI-powered technical analysis assistant. Send me any trading chart and I'll provide detailed technical analysis including:

- 📈 Trend direction and market bias
- 🎯 Support and resistance levels  
- 📐 Chart patterns identification
- 📊 Volume analysis (if visible)
- 🎪 Price targets and stop losses
- ⚠️ Risk assessment

**Daily Limit:** 3 free analyses per day
**Need more?** Upgrade for additional analyses

Use /analyze to get started or /help for more information.
    """,
    
    'help_message': """
📚 **How to Use Chart Analyzer**

**Commands:**
- /start - Welcome message and main menu
- /analyze - Start chart analysis
- /status - Check your usage statistics
- /help - Show this help message

**How to analyze charts:**
1. Send the /analyze command
2. Upload your chart image (PNG, JPG, or JPEG)
3. Wait for the AI analysis (usually 10-30 seconds)
4. Review the detailed technical analysis

**Supported formats:** PNG, JPG, JPEG (max 5MB)
**Daily limit:** 3 free analyses per day
**Upgrade options:** Get 10 more analyses for $5

Need help? Contact @support
    """
}

# Load configuration instance
config = Config()
