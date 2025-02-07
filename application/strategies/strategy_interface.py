from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd
from trading_platform.domain.models.instrument import Instrument, Signal

class TradingStrategy(ABC):
    @abstractmethod
    async def analyze(self, 
                     market_data: pd.DataFrame,
                     instrument: Instrument) -> Optional[Signal]:
        pass
