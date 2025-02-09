from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ScannerConfig:
    symbols: Optional[List[str]] = None
    batch_size: int = 100
    min_volume: int = 1_000_000
    min_price: float = 5.0
    max_price: float = 1000.0
    min_volatility: float = 0.15
    max_volatility: float = 0.50
    momentum_lookback: int = 5
    min_momentum: float = 0.02

class Config:
    def __init__(self):
        self.scanner = ScannerConfig()

@dataclass
class NewsConfig:
    alpha_vantage_key: str = ""
    finnhub_key: str = ""
    min_sentiment_score: float = 0.2
    min_news_volume: float = 0.3
    days_to_analyze: int = 7

class Config:
    def __init__(self):
        self.scanner = ScannerConfig()
        self.news = NewsConfig()