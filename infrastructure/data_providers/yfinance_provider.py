import asyncio
from datetime import datetime
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
from ratelimit import limits, sleep_and_retry
import logging
from .provider_interface import MarketDataProvider
from trading_platform.domain.models.instrument import Instrument
from trading_platform.config import Config, RequestTracker

logger = logging.getLogger(__name__)

class DataProviderError(Exception):
    pass

class YFinanceProvider(MarketDataProvider):
    def __init__(self, config: Config, request_tracker: RequestTracker):
        self.config = config
        self.request_tracker = request_tracker
        self.executor = ThreadPoolExecutor()

    @sleep_and_retry
    @limits(calls=1, period=1)
    async def get_historical_data(self,
                                instrument: Instrument,
                                start_date: datetime,
                                end_date: datetime,
                                interval: str = '1d') -> pd.DataFrame:
        try:
            self.request_tracker.log_stock_request()
            stock = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: yf.Ticker(instrument.symbol)
            )
            
            df = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: stock.history(start=start_date, end=end_date, interval=interval)
            )
            
            return df
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            raise DataProviderError(f"Failed to fetch data for {instrument.symbol}")
            
    async def get_options_data(self, instrument: Instrument):  # Removed return type hint
        try:
            self.request_tracker.log_options_request()
            stock = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: yf.Ticker(instrument.symbol)
            )
            
            options_data = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: stock.options
            )
            
            return {'expiration_dates': options_data}
        except Exception as e:
            logger.error(f"Error fetching options data: {str(e)}")
            raise DataProviderError(f"Failed to fetch options data for {instrument.symbol}")