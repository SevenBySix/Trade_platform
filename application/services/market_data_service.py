from datetime import datetime
from typing import Optional
import pandas as pd
from trading_platform.domain.models.instrument import Instrument
from trading_platform.domain.events.market_event import MarketEvent
from trading_platform.infrastructure.data_providers.provider_interface import MarketDataProvider

class Cache:
    async def get(self, key: str):
        pass
    
    async def set(self, key: str, value: any):
        pass

class EventBus:
    async def publish(self, event: any):
        pass

class MarketDataService:
    def __init__(self,
                 provider: MarketDataProvider,
                 cache: Optional[Cache] = None,
                 event_bus: Optional[EventBus] = None):
        self.provider = provider
        self.cache = cache
        self.event_bus = event_bus

    async def get_market_data(self,
                            instrument: Instrument,
                            start_date: datetime,
                            end_date: datetime) -> pd.DataFrame:
        cache_key = f"{instrument.symbol}:{start_date}:{end_date}"
        
        if self.cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data

        data = await self.provider.get_historical_data(
            instrument, start_date, end_date
        )
        
        if self.cache:
            await self.cache.set(cache_key, data)
            
        if self.event_bus:
            await self.event_bus.publish(
                MarketEvent(
                    instrument=instrument,
                    event_type="DATA_FETCHED",
                    data=data,
                    timestamp=datetime.now()
                )
            )
            
        return data
