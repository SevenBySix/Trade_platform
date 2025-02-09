from typing import List, Dict
import logging
from datetime import datetime
from ..config.config import Config
from ...infrastructure.apis.news_providers.base import NewsProvider

logger = logging.getLogger(__name__)

class NewsAnalyzer:
    def __init__(self, config: Config, providers: List[NewsProvider]):
        self.config = config
        self.providers = providers
        
    async def analyze_stock_news(self, symbol: str, days_back: int = 7) -> Dict:
        """Analyze news from all providers for a given stock"""
        all_news = []
        
        # Gather news from all providers
        for provider in self.providers:
            try:
                news = await provider.get_news(symbol, days_back)
                all_news.extend(news)
            except Exception as e:
                logger.error(f"Error getting news from provider for {symbol}: {str(e)}")
        
        if not all_news:
            return {
                'has_significant_news': False,
                'sentiment_score': 0,
                'news_volume_score': 0,
                'recent_news': []
            }
        
        # Sort by date and calculate metrics
        all_news.sort(key=lambda x: x['date'], reverse=True)
        
        # Calculate aggregate sentiment
        sentiments = [n['sentiment'] for n in all_news if 'sentiment' in n]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        # Calculate news volume score (more recent news = higher score)
        now = datetime.now()
        news_volume_score = sum(
            1 / (abs((datetime.fromisoformat(n['date']) - now).days) + 1)
            for n in all_news
        )
        
        return {
            'has_significant_news': len(all_news) > 2 and abs(avg_sentiment) > 0.2,
            'sentiment_score': avg_sentiment,
            'news_volume_score': min(news_volume_score / 5, 1.0),  # Normalize to 0-1
            'recent_news': all_news[:5]  # Return 5 most recent news items
        }
    
    def get_news_summary(self, news_data: Dict) -> str:
        """Generate a human-readable summary of news analysis"""
        if not news_data['has_significant_news']:
            return "No significant news found"
            
        sentiment_str = (
            "positive" if news_data['sentiment_score'] > 0.2
            else "negative" if news_data['sentiment_score'] < -0.2
            else "neutral"
        )
        
        volume_str = (
            "high" if news_data['news_volume_score'] > 0.7
            else "moderate" if news_data['news_volume_score'] > 0.3
            else "low"
        )
        
        return f"{volume_str} news volume with {sentiment_str} sentiment"