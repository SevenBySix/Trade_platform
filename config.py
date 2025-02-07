from dataclasses import dataclass
import logging
import threading
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

@dataclass
class Config:
    # Analysis thresholds
    min_prediction_confidence: float = 0.75  # Increased from 0.60
    min_profit_threshold: float = 0.20      # Increased from 0.15
    max_risk_threshold: float = 0.35        # Reduced from 0.60
    max_option_price: float = 25.00         # Increased from 10.00
    min_volume: int = 1000                  # Increased from 10
    min_open_interest: int = 500            # Increased from 50
    days_to_expiry_min: int = 14           # Increased from 7
    days_to_expiry_max: int = 45           # Reduced from 60
    
    # Market condition thresholds
    max_volatility: float = 0.30           # Maximum acceptable volatility
    min_rsi: float = 30                    # Minimum RSI for buy signals
    max_rsi: float = 70                    # Maximum RSI for buy signals
    
    # Rate limiting
    stock_requests_per_hour: int = 875
    options_requests_per_hour: int = 875
    seconds_between_stock_requests: float = 4.11
    seconds_between_options_requests: float = 4.11
    
    # Symbols to analyze
    symbols: list = None

class RequestTracker:
    def __init__(self):
        self.stock_requests = 0
        self.options_requests = 0
        self.start_time = datetime.now()
        self.lock = threading.Lock()

    def log_stock_request(self):
        with self.lock:
            self.stock_requests += 1
            self._check_reset()

    def log_options_request(self):
        with self.lock:
            self.options_requests += 1
            self._check_reset()

    def _check_reset(self):
        current_time = datetime.now()
        elapsed_hours = (current_time - self.start_time).total_seconds() / 3600
        
        if elapsed_hours >= 1:
            logger.info(f"Hourly Request Count - Stocks: {self.stock_requests}, Options: {self.options_requests}")
            self.stock_requests = 0
            self.options_requests = 0
            self.start_time = current_time
