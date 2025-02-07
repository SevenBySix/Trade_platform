import asyncio
from datetime import datetime, timedelta
from trading_platform.config import Config, RequestTracker
from trading_platform.domain.models.instrument import Instrument
from trading_platform.infrastructure.data_providers.yfinance_provider import YFinanceProvider
from trading_platform.application.services.market_data_service import MarketDataService
from trading_platform.application.services.analysis_service import AnalysisService, OptionsAnalyzer
from trading_platform.application.strategies.ml_strategy import MLTradingStrategy

async def main():
    # Load configuration
    config = Config()
    config.symbols = ['AAPL', 'MSFT', 'GOOGL']  # Example symbols
    
    # Set up infrastructure
    request_tracker = RequestTracker()
    data_provider = YFinanceProvider(config, request_tracker)
    market_data_service = MarketDataService(data_provider)
    
    # Set up strategies
    strategies = [
        MLTradingStrategy(config)
    ]
    
    # Set up analysis service
    analysis_service = AnalysisService(
        market_data_service=market_data_service,
        strategies=strategies,
        options_analyzer=OptionsAnalyzer()
    )
    
    # Process instruments
    instruments = [
        Instrument(symbol=symbol)
        for symbol in config.symbols
    ]
    
    for instrument in instruments:
        # Fetch 200 days of data to ensure enough history for analysis
        signals = await analysis_service.analyze_instrument(
            instrument,
            start_date=datetime.now() - timedelta(days=200),  # Increased from 30 to 200 days
            end_date=datetime.now()
        )
        
        for signal in signals:
            print(f"\nGenerated signal for {signal.instrument.symbol}:")
            print(f"Type: {signal.type}")
            print(f"Confidence: {signal.confidence:.2%}")
            print(f"Price: ${float(signal.price):.2f}")
            print("\nTechnical Indicators:")
            for indicator, value in signal.technical_indicators.items():
                print(f"{indicator}: {value:.2f}")
            print("\nReasons:")
            for reason in signal.reason:
                print(f"- {reason}")
            if signal.options_data:
                print(f"\nFound {len(signal.options_data)} promising options")

if __name__ == "__main__":
    asyncio.run(main())