from datetime import datetime
from collections.abc import Sequence
import logging
from trading_platform.domain.models.instrument import Instrument, Signal
from trading_platform.domain.events.market_event import SignalEvent
from .market_data_service import MarketDataService, EventBus
from ..strategies.strategy_interface import TradingStrategy

logger = logging.getLogger(__name__)

class OptionsAnalyzer:
    async def analyze(self, instrument: Instrument, price: float) -> list[dict]:  # Python 3.9+ syntax
        return []

class AnalysisService:
    def __init__(self,
                 market_data_service: MarketDataService,
                 strategies: Sequence[TradingStrategy],
                 options_analyzer: OptionsAnalyzer | None = None,  # Python 3.10+ union type
                 event_bus: EventBus | None = None):
        self.market_data_service = market_data_service
        self.strategies = strategies
        self.options_analyzer = options_analyzer
        self.event_bus = event_bus

    async def analyze_instrument(self,
                               instrument: Instrument,
                               start_date: datetime,
                               end_date: datetime) -> list[Signal]:
        try:
            # Fetch market data
            market_data = await self.market_data_service.get_market_data(
                instrument, start_date, end_date
            )
            
            signals = []
            
            # Apply each strategy
            for strategy in self.strategies:
                signal = await strategy.analyze(market_data, instrument)
                if signal:
                    # Add options analysis if available
                    if self.options_analyzer:
                        options_data = await self.options_analyzer.analyze(
                            instrument, signal.price
                        )
                        signal.options_data = options_data
                    
                    signals.append(signal)
                    
                    # Publish signal event
                    if self.event_bus:
                        await self.event_bus.publish(
                            SignalEvent(signal=signal, timestamp=datetime.now())
                        )
            
            return signals

        except Exception as e:
            logger.error(f"Error analyzing instrument {instrument.symbol}: {str(e)}")
            return []