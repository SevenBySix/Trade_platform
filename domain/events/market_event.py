from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict
from ..models.instrument import Instrument, Signal

@dataclass
class MarketEvent:
    instrument: Instrument
    price: Decimal
    timestamp: datetime
    event_type: str
    data: Dict = None

@dataclass
class SignalEvent:
    signal: Signal
    timestamp: datetime
