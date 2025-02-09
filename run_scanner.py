import asyncio
import os
from dotenv import load_dotenv
from trading_platform.application.config.config import Config
from trading_platform.application.scanners.market_scanner import MarketScanner

def load_configuration() -> Config:
    # Load environment variables
    load_dotenv()
    
    config = Config()
    
    # API Keys
    config.news.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY')
    config.news.finnhub_key = os.getenv('FINNHUB_KEY')
    
    # Scanner Configuration
    config.scanner.min_volume = int(os.getenv('MIN_VOLUME', 1000000))
    config.scanner.min_price = float(os.getenv('MIN_PRICE', 5.0))
    config.scanner.max_price = float(os.getenv('MAX_PRICE', 1000.0))
    config.scanner.min_volatility = float(os.getenv('MIN_VOLATILITY', 0.15))
    config.scanner.max_volatility = float(os.getenv('MAX_VOLATILITY', 0.50))
    
    # News Configuration
    config.news.days_to_analyze = int(os.getenv('NEWS_DAYS_TO_ANALYZE', 7))
    config.news.min_sentiment_score = float(os.getenv('MIN_SENTIMENT_SCORE', 0.2))
    config.news.min_news_volume = float(os.getenv('MIN_NEWS_VOLUME', 0.3))
    
    return config

async def main():
    # Load configuration
    config = load_configuration()
    
    # Initialize scanner
    scanner = MarketScanner(config)
    
    try:
        # Run market scan
        promising_stocks = await scanner.scan_market()
        
        # Print results
        print("\nPromising Stocks Found:")
        print("=" * 50)
        for stock in promising_stocks:
            print(f"\nSymbol: {stock['symbol']}")
            print(f"Company: {stock['company_name']}")
            print(f"Price: ${stock['current_price']:.2f}")
            print(f"Volume: {stock['volume']:,}")
            print("\nReasons:")
            for reason in stock['reasons']:
                print(f"- {reason}")
            
            if 'news_data' in stock and stock['news_data']['recent_news']:
                print("\nRecent News:")
                for news in stock['news_data']['recent_news'][:3]:
                    print(f"- {news['title']}")
            
            print("-" * 50)
            
    except Exception as e:
        print(f"Error during market scan: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())