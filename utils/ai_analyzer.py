"""
AI Chart Analyzer using OpenAI GPT-4 Vision
"""
import json
import logging
import base64
import asyncio
import os
from typing import Dict, Any, Optional
from datetime import datetime
import httpx
from openai import AsyncOpenAI

from utils.image_handler import img_to_base64
from bot.utils.data_fetcher import fetch_ohlcv
from bot.utils.tech_indicators import build_indicator_snapshot
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _detect_symbol_tf(img_path: str) -> tuple[str, str] | None:
    """
    Quick fallback until OCR is ready.
    ex:  BTCUSDT_1h.png  →  ('BINANCE:BTCUSDT', '1h')
    """
    stem = Path(img_path).stem.lower()
    for tf in ("1m","5m","15m","30m","1h","4h","1d","1w"):
        if stem.endswith(tf):
            symbol = stem[: -len(tf) - 1]   # remove '_' + tf
            return f"BINANCE:{symbol.upper()}", tf
    return None


# Chart Analysis Prompt
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

class AIAnalyzer:
    """AI-powered chart analysis using GPT-4 Vision"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key or not self.api_key.startswith('sk-'):
            logger.warning("⚠️ No valid OpenAI API key found")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)
            logger.info("✅ OpenAI client initialized")
        
        self.model = "gpt-4o"
        self.max_tokens = 1000
        self.temperature = 0.1
        
    async def analyze_chart(self, image_path: str, user_id: int) -> Dict[str, Any]:
        """
        Analyze a chart image and return structured analysis
        
        Args:
            image_path: Path to the image file
            user_id: Telegram user ID for tracking
            
        Returns:
            Dictionary containing analysis results
        """
        start_time = datetime.now()
        
        try:
            if not self.client:
                return self._get_no_api_key_response()
            
            logger.info(f"🤖 Starting chart analysis for user {user_id}")
            
            # Prepare image for analysis
            base64_image = await self._prepare_image(image_path)
            if not base64_image:
                return self._get_error_response("Failed to prepare image")
            
            # Call OpenAI API
            analysis_result = await self._call_openai_api(base64_image)
            
            # Process and validate response
            processed_result = await self._process_analysis_result(analysis_result)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            processed_result['processing_time'] = processing_time
            
            logger.info(f"✅ Chart analysis completed for user {user_id} in {processing_time:.2f}s")
            
            return processed_result
            
        except Exception as e:
            logger.error(f"❌ Chart analysis failed for user {user_id}: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return self._get_error_response(str(e), processing_time)
    
    async def _prepare_image(self, image_path: str) -> Optional[str]:
        """Prepare image for OpenAI API by encoding to base64"""
        try:
            with open(image_path, 'rb') as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                
            logger.info(f"✅ Image prepared for analysis: {len(base64_image)} chars")
            return base64_image
            
        except Exception as e:
            logger.error(f"❌ Error preparing image: {str(e)}")
            return None
    
    async def _call_openai_api(self, base64_image: str) -> Dict[str, Any]:
        """Call OpenAI API with retry logic"""
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Calling OpenAI API (attempt {attempt + 1})")
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": CHART_ANALYSIS_PROMPT
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}",
                                        "detail": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    response_format={"type": "json_object"}
                )
                
                logger.info("✅ OpenAI API call successful")
                
                return {
                    'success': True,
                    'content': response.choices[0].message.content,
                    'usage': response.usage.model_dump() if response.usage else None
                }
                
            except Exception as e:
                logger.warning(f"⚠️ OpenAI API attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    raise
    
    async def _process_analysis_result(self, api_result: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate OpenAI API response"""
        try:
            if not api_result.get('success'):
                raise ValueError("API call failed")
            
            # Parse JSON response
            content = api_result.get('content', '{}')
            analysis_data = json.loads(content)
            
            # Validate and normalize data
            analysis_data = self._validate_analysis_data(analysis_data)
            
            # Add metadata
            analysis_data['success'] = True
            analysis_data['api_usage'] = api_result.get('usage')
            analysis_data['generated_at'] = datetime.now().isoformat()
            
            return analysis_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {str(e)}")
            return self._get_error_response(f"Invalid JSON response: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error processing analysis result: {str(e)}")
            return self._get_error_response(str(e))
    
    def _validate_analysis_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize analysis data"""
        # Set defaults for required fields
        validated = {
            'trend': data.get('trend', 'sideways').lower(),
            'confidence': float(data.get('confidence', 0.5)),
            'market_bias': data.get('market_bias', 'neutral').lower(),
            'risk_level': data.get('risk_level', 'medium').lower(),
            'support_levels': [],
            'resistance_levels': [],
            'price_targets': [],
            'patterns': [],
            'volume_analysis': data.get('volume_analysis'),
            'indicators': data.get('indicators'),
            'key_insights': data.get('key_insights', 'Analysis completed.'),
            'timeframe_detected': data.get('timeframe_detected'),
            'stop_loss_level': data.get('stop_loss_level'),
            'summary': data.get('summary', 'Chart analysis completed.')
        }
        
        # Validate trend
        if validated['trend'] not in ['uptrend', 'downtrend', 'sideways']:
            validated['trend'] = 'sideways'
        
        # Validate confidence
        if not 0 <= validated['confidence'] <= 1:
            validated['confidence'] = 0.5
        
        # Validate price levels
        for level_key in ['support_levels', 'resistance_levels', 'price_targets']:
            levels = data.get(level_key, [])
            if isinstance(levels, list):
                validated[level_key] = [float(level) for level in levels if isinstance(level, (int, float))]
        
        # Validate patterns
        patterns = data.get('patterns', [])
        if isinstance(patterns, list):
            validated['patterns'] = [str(pattern) for pattern in patterns if pattern]
        
        # Validate risk level
        if validated['risk_level'] not in ['low', 'medium', 'high']:
            validated['risk_level'] = 'medium'
        
        # Validate market bias
        if validated['market_bias'] not in ['bullish', 'bearish', 'neutral']:
            validated['market_bias'] = 'neutral'
        
        return validated
    
    def _get_error_response(self, error_message: str, processing_time: float = 0) -> Dict[str, Any]:
        """Get standardized error response"""
        return {
            'success': False,
            'error': error_message,
            'trend': 'sideways',
            'confidence': 0.0,
            'market_bias': 'neutral',
            'risk_level': 'medium',
            'support_levels': [],
            'resistance_levels': [],
            'price_targets': [],
            'patterns': [],
            'volume_analysis': None,
            'indicators': None,
            'key_insights': 'Unable to analyze chart due to technical issues.',
            'timeframe_detected': None,
            'stop_loss_level': None,
            'summary': 'Analysis could not be completed.',
            'processing_time': processing_time,
            'generated_at': datetime.now().isoformat()
        }
    
    def _get_no_api_key_response(self) -> Dict[str, Any]:
        """Get response when no API key is available"""
        return {
            'success': False,
            'error': 'OpenAI API key not configured',
            'trend': 'uptrend',
            'confidence': 0.75,
            'market_bias': 'bullish',
            'risk_level': 'medium',
            'support_levels': [42150.0, 41800.0],
            'resistance_levels': [43500.0, 44200.0],
            'price_targets': [44800.0, 45500.0],
            'patterns': ['ascending triangle'],
            'volume_analysis': 'Volume data not available in demo mode',
            'indicators': 'Technical indicators show bullish momentum',
            'key_insights': 'Demo analysis - configure OpenAI API key for real analysis.',
            'timeframe_detected': '1h',
            'stop_loss_level': 41500.0,
            'summary': 'Demo analysis showing bullish trend. Configure OpenAI API key for real analysis.',
            'processing_time': 1.5,
            'generated_at': datetime.now().isoformat()
        }
    
    def format_analysis_message(self, analysis: Dict[str, Any]) -> str:
        """Format analysis result for Telegram message"""
        if not analysis.get('success', True):
            return f"❌ **Analysis Failed**\n\n{analysis.get('error', 'Unknown error')}\n\nPlease try again with a different image."
        
        # Emoji mapping
        trend_emoji = {
            'uptrend': '📈',
            'downtrend': '📉',
            'sideways': '📊'
        }
        
        bias_emoji = {
            'bullish': '🐂',
            'bearish': '🐻',
            'neutral': '⚖️'
        }
        
        risk_emoji = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🔴'
        }
        
        # Build message
        trend = analysis.get('trend', 'sideways')
        confidence = analysis.get('confidence', 0.5)
        market_bias = analysis.get('market_bias', 'neutral')
        risk_level = analysis.get('risk_level', 'medium')
        
        message = f"📊 **Chart Analysis Results**\n\n"
        
        # Main analysis
        message += f"{trend_emoji.get(trend, '📊')} **Trend:** {trend.title()}\n"
        message += f"{bias_emoji.get(market_bias, '⚖️')} **Market Bias:** {market_bias.title()}\n"
        message += f"🎯 **Confidence:** {confidence:.0%}\n"
        message += f"{risk_emoji.get(risk_level, '🟡')} **Risk Level:** {risk_level.title()}\n\n"
        
        # Price levels
        support_levels = analysis.get('support_levels', [])
        resistance_levels = analysis.get('resistance_levels', [])
        
        if support_levels:
            levels_text = ', '.join([f"${level:,.2f}" for level in support_levels[:3]])
            message += f"🟢 **Support:** {levels_text}\n"
        
        if resistance_levels:
            levels_text = ', '.join([f"${level:,.2f}" for level in resistance_levels[:3]])
            message += f"🔴 **Resistance:** {levels_text}\n"
        
        # Patterns
        patterns = analysis.get('patterns', [])
        if patterns:
            message += f"📐 **Patterns:** {', '.join(patterns[:3])}\n"
        
        # Targets and stop loss
        price_targets = analysis.get('price_targets', [])
        stop_loss = analysis.get('stop_loss_level')
        
        if price_targets:
            targets_text = ', '.join([f"${target:,.2f}" for target in price_targets[:2]])
            message += f"🎯 **Targets:** {targets_text}\n"
        
        if stop_loss:
            message += f"🛑 **Stop Loss:** ${stop_loss:,.2f}\n"
        
        # Timeframe
        timeframe = analysis.get('timeframe_detected')
        if timeframe:
            message += f"⏱️ **Timeframe:** {timeframe.upper()}\n"
        
        message += "\n"
        
        # Key insights
        key_insights = analysis.get('key_insights')
        if key_insights:
            message += f"💡 **Key Insights:**\n{key_insights}\n\n"
        
        # Summary
        summary = analysis.get('summary', 'Analysis completed.')
        message += f"📝 **Summary:**\n{summary}\n\n"
        
        # Processing time
        processing_time = analysis.get('processing_time')
        if processing_time:
            message += f"⚡ *Analysis completed in {processing_time:.1f}s*\n"
        
        # API key status
        if 'demo' in analysis.get('key_insights', '').lower():
            message += "\n🔧 *Add OpenAI API key for real analysis*\n"
        
        # Disclaimer
        message += "\n⚠️ *This analysis is for educational purposes only.*"
        
        return message

# Create singleton instance
ai_analyzer = AIAnalyzer()
