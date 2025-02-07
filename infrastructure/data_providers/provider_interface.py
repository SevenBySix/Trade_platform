from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd
from trading_platform.domain.models.instrument import Instrument

class MarketDataProvider(ABC):
    @abstractmethod
    async def get_historical_data(self, 
                                instrument: Instrument,
                                start_date: datetime,
                                end_date: datetime,
                                interval: str = '1d') -> pd.DataFrame:
        pass
    
    @abstractmethod
    async def get_options_data(self, instrument: Instrument) -> dict:  # Python 3.9+ syntax
        pass