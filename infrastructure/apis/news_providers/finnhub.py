import aiohttp
import logging
from datetime import datetime, timedelta
from .base import NewsProvider
from ...utils.async_utils import async_retry

logger = logging.getLogger(__name__)

class FinnHubNews(NewsProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1/company-news"

    @async_retry(retries=3, delay=1.0)
    async def get_news(self, symbol: str, days_back: int = 7) -> List[Dict]:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        headers = {
            "X-Finnhub-Token": self.api_key
        }
        
        params = {
            "symbol": symbol,
            "from": start_date.strftime('%Y-%m-%d'),
            "to": end_date.strftime('%Y-%m-%d')
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_news(data)
                    else:
                        logger.error(f"Error fetching news for {symbol}: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error in news fetch: {str(e)}")
            return []

    def _process_news(self, articles: List[Dict]) -> List[Dict]:
        try:
            processed_news = []
            
            for article in articles:
                processed_news.append({
                    'title': article['headline'],
                    'summary': article['summary'],
                    'source': article['source'],
                    'url': article['url'],
                    'date': datetime.fromtimestamp(article['datetime']).isoformat(),
                    'sentiment': self._calculate_sentiment(article['summary']),
                    'relevance': 1.0  # FinnHub doesn't provide relevance scores
                })

            return processed_news

        except Exception as e:
            logger.error(f"Error processing news data: {str(e)}")
            return []

    def _calculate_sentiment(self, text: str) -> float:
        # Simple sentiment calculation - replace with more sophisticated analysis
        # Returns a value between -1 and 1
        positive_words = {'up', 'rise', 'gain', 'positive', 'growth', 'surge'}
        negative_words = {'down', 'fall', 'loss', 'negative', 'decline', 'drop'}
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total = positive_count + negative_count
        if total == 0:
            return 0
            
        return (positive_count - negative_count) / total