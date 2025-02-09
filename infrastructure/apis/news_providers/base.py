from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime

class NewsProvider(ABC):
    @abstractmethod
    async def get_news(self, symbol: str, days_back: int = 7) -> List[Dict]:
        """Get news for a specific symbol"""
        pass