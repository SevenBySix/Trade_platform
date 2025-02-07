import asyncio
import logging
from colorama import init
from trading_platform.application.config.config import Config
from trading_platform.application.scanners.market_scanner import MarketScanner

# Initialize colorama
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

async def main():
    # Initialize configuration
    config = Config()
    
    # Create scanner
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
            print("-" * 50)
            
    except Exception as e:
        logging.error(f"Error during market scan: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
