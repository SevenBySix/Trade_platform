from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, List

@dataclass(frozen=True)
class Instrument:
    symbol: str
    type: str = "stock"  # stock, option, etc.
    exchange: str = "NYSE"

@dataclass
class MarketData:
    instrument: Instrument
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    timestamp: datetime
    additional_data: Dict = None

@dataclass
class Signal:
    instrument: Instrument
    type: str  # BUY, SELL
    confidence: float
    timestamp: datetime
    price: Decimal
    technical_indicators: Dict[str, float]
    prediction: float
    options_data: Optional[List[Dict]] = None
    reason: List[str] = None
