import aiohttp
import logging
from datetime import datetime, timedelta
from .base import NewsProvider
from ...utils.async_utils import async_retry

logger = logging.getLogger(__name__)

class AlphaVantageNews(NewsProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"

    @async_retry(retries=3, delay=1.0)
    async def get_news(self, symbol: str, days_back: int = 7) -> List[Dict]:
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": symbol,
            "apikey": self.api_key,
            "limit": 50  # Adjust based on your needs
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_news(data, days_back)
                    else:
                        logger.error(f"Error fetching news for {symbol}: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error in news fetch: {str(e)}")
            return []

    def _process_news(self, data: Dict, days_back: int) -> List[Dict]:
        try:
            if 'feed' not in data:
                return []

            cutoff_date = datetime.now() - timedelta(days=days_back)
            processed_news = []

            for article in data['feed']:
                pub_date = datetime.strptime(article['time_published'], '%Y%m%dT%H%M%S')
                if pub_date >= cutoff_date:
                    processed_news.append({
                        'title': article['title'],
                        'summary': article['summary'],
                        'source': article['source'],
                        'url': article['url'],
                        'date': pub_date.isoformat(),
                        'sentiment': article.get('overall_sentiment_score', 0),
                        'relevance': article.get('relevance_score', 0)
                    })

            return processed_news

        except Exception as e:
            logger.error(f"Error processing news data: {str(e)}")
            return []
