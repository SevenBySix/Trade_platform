from typing import List, Dict, Set
import logging
import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from colorama import init, Fore, Style
from ..config.config import Config
from ...infrastructure.apis.news_providers.alpha_vantage import AlphaVantageNews
from ...infrastructure.apis.news_providers.finnhub import FinnHubNews
from ..news.news_analyzer import NewsAnalyzer

# Initialize colorama
init()

class ColoredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def info(self, msg):
        self.logger.info(f"{Fore.GREEN}{msg}{Style.RESET_ALL}")

    def warning(self, msg):
        self.logger.warning(f"{Fore.YELLOW}{msg}{Style.RESET_ALL}")

    def error(self, msg):
        self.logger.error(f"{Fore.RED}{msg}{Style.RESET_ALL}")

    def success(self, msg):
        self.logger.info(f"{Fore.CYAN}{msg}{Style.RESET_ALL}")

class MarketScanner:
    def __init__(self, config: Config):
        self.config = config
        self.logger = ColoredLogger(__name__)
        self.filters = self._initialize_filters()
        
        # Initialize news providers
        self.news_providers = []
        if config.news.alpha_vantage_key:
            self.news_providers.append(
                AlphaVantageNews(config.news.alpha_vantage_key)
            )
        if config.news.finnhub_key:
            self.news_providers.append(
                FinnHubNews(config.news.finnhub_key)
            )
        
        # Initialize news analyzer
        self.news_analyzer = NewsAnalyzer(config, self.news_providers)
        
    def _initialize_filters(self) -> Dict:
        """Initialize filtering criteria"""
        return {
            'volume': {
                'min': 1_000_000,        # Minimum daily volume
                'surge_factor': 1.5      # Recent volume vs average
            },
            'price': {
                'min': 5.0,              # Minimum price
                'max': 1000.0            # Maximum price
            },
            'volatility': {
                'min': 0.15,             # Minimum annualized volatility
                'max': 0.50              # Maximum annualized volatility
            },
            'momentum': {
                'lookback_days': 5,      # Days to look back
                'min_return': 0.02       # Minimum return over period
            },
            'technical': {
                'sma_periods': [20, 50], # Moving averages to check
                'rsi_period': 14,        # RSI period
                'rsi_thresholds': {      # RSI thresholds
                    'oversold': 30,
                    'overbought': 70
                }
            }
        }

    async def get_tradable_universe(self) -> Set[str]:
        """Get list of tradable stocks from various sources"""
        self.logger.info("Fetching tradable universe...")
        tradable_stocks = set()
        
        indices = {
            '^GSPC': 'S&P 500',
            '^NDX': 'NASDAQ 100',
            '^RUT': 'Russell 2000'
        }
        
        for index_symbol, index_name in indices.items():
            try:
                self.logger.info(f"Fetching {index_name} components...")
                index = yf.Ticker(index_symbol)
                components = self._mock_get_index_components(index_name)
                tradable_stocks.update(components)
                self.logger.success(f"Added {len(components)} stocks from {index_name}")
            except Exception as e:
                self.logger.error(f"Error fetching {index_name} components: {str(e)}")
        
        self.logger.success(f"Found {len(tradable_stocks)} total tradable stocks")
        return tradable_stocks

    def _mock_get_index_components(self, index_name: str) -> Set[str]:
        """Mock function to return index components - replace with real data source"""
        if index_name == 'S&P 500':
            return {'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'}  # Example stocks
        return set()

    async def scan_market(self) -> List[Dict]:
        """Main scanning function that finds promising stocks"""
        self.logger.info("Starting market scan...")
        promising_stocks = []
        tradable_universe = await self.get_tradable_universe()
        
        # Process stocks in batches
        batch_size = 100
        total_batches = (len(tradable_universe) + batch_size - 1) // batch_size
        
        for batch_num, i in enumerate(range(0, len(tradable_universe), batch_size), 1):
            batch = list(tradable_universe)[i:i+batch_size]
            self.logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} stocks)")
            
            # Get initial metrics
            metrics = await self._get_batch_metrics(batch)
            
            # Apply initial filters
            filtered_batch = []
            for symbol, metric in metrics.items():
                if self._passes_initial_filters(metric):
                    filtered_batch.append(symbol)
            
            if filtered_batch:
                self.logger.success(f"Found {len(filtered_batch)} stocks passing initial filters")
                
                # Detailed analysis of remaining stocks
                for symbol in filtered_batch:
                    try:
                        if await self._detailed_analysis(symbol):
                            stock_data = await self._gather_stock_data(symbol)
                            # Add news analysis
                            stock_data = await self._analyze_with_news(symbol, stock_data)
                            promising_stocks.append(stock_data)
                            self.logger.success(f"Added promising stock: {symbol}")
                    except Exception as e:
                        self.logger.error(f"Error analyzing {symbol}: {str(e)}")
            
            await asyncio.sleep(1)  # Rate limiting
        
        self.logger.success(f"Scan complete. Found {len(promising_stocks)} promising stocks")
        return promising_stocks

    async def _get_batch_metrics(self, symbols: List[str]) -> Dict:
        """Get basic metrics for a batch of symbols"""
        metrics = {}
        for symbol in symbols:
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(period="60d")
                if len(hist) > 0:
                    metrics[symbol] = {
                        'price': hist['Close'][-1],
                        'volume': hist['Volume'][-1],
                        'avg_volume': hist['Volume'].mean(),
                        'volatility': hist['Close'].pct_change().std() * np.sqrt(252)
                    }
            except Exception as e:
                self.logger.error(f"Error fetching metrics for {symbol}: {str(e)}")
        return metrics

    def _passes_initial_filters(self, metrics: Dict) -> bool:
        """Apply basic filters to quickly eliminate unsuitable stocks"""
        filters = self.filters
        
        # Price filter
        if not (filters['price']['min'] <= metrics['price'] <= filters['price']['max']):
            return False
            
        # Volume filter
        if metrics['volume'] < filters['volume']['min']:
            return False
            
        # Volatility filter
        if not (filters['volatility']['min'] <= metrics['volatility'] <= filters['volatility']['max']):
            return False
            
        return True

    async def _detailed_analysis(self, symbol: str) -> bool:
        """Perform deeper analysis on stocks that passed initial filters"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="60d")
            
            if len(hist) < 60:
                return False
                
            # Calculate technical indicators
            sma_20 = hist['Close'].rolling(window=20).mean()
            sma_50 = hist['Close'].rolling(window=50).mean()
            rsi = self._calculate_rsi(hist['Close'])
            
            conditions = [
                hist['Volume'][-5:].mean() > hist['Volume'].mean() * self.filters['volume']['surge_factor'],
                hist['Close'][-1] > sma_20[-1],  # Price above 20-day MA
                sma_20[-1] > sma_50[-1],         # 20-day MA above 50-day MA
                30 <= rsi[-1] <= 70,             # RSI not extreme
                self._calculate_momentum(hist) > self.filters['momentum']['min_return']
            ]
            
            return all(conditions)
            
        except Exception as e:
            self.logger.error(f"Error in detailed analysis for {symbol}: {str(e)}")
            return False

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_momentum(self, hist: pd.DataFrame) -> float:
        """Calculate price momentum"""
        lookback = self.filters['momentum']['lookback_days']
        return (hist['Close'][-1] / hist['Close'][-lookback] - 1)

    async def _gather_stock_data(self, symbol: str) -> Dict:
        """Gather comprehensive data for promising stocks"""
        stock = yf.Ticker(symbol)
        hist = stock.history(period="60d")
        
        info = {
            'symbol': symbol,
            'company_name': stock.info.get('longName', ''),
            'sector': stock.info.get('sector', ''),
            'market_cap': stock.info.get('marketCap', 0),
            'current_price': hist['Close'][-1],
            'volume': hist['Volume'][-1],
            'scan_time': datetime.now().isoformat(),
            'technical_data': {
                'momentum': self._calculate_momentum(hist),
                'volatility': hist['Close'].pct_change().std() * np.sqrt(252),
                'rsi': self._calculate_rsi(hist['Close'])[-1],
                'volume_surge': hist['Volume'][-5:].mean() / hist['Volume'].mean()
            }
        }
        
        info['reasons'] = self._generate_scan_reason(info)
        return info

    def _generate_scan_reason(self, info: Dict) -> List[str]:
        """Generate explanations for why this stock was selected"""
        reasons = []
        tech_data = info['technical_data']
        
        # Volume analysis
        if tech_data['volume_surge'] > self.filters['volume']['surge_factor']:
            reasons.append(f"Volume surge: {tech_data['volume_surge']:.1f}x average")
        
        # Momentum
        if tech_data['momentum'] > self.filters['momentum']['min_return']:
            reasons.append(f"Strong momentum: {tech_data['momentum']:.1%}")
        
        # RSI
        if 40 <= tech_data['rsi'] <= 60:
            reasons.append(f"Neutral RSI: {tech_data['rsi']:.1f}")
        
        # Volatility
        if self.filters['volatility']['min'] <= tech_data['volatility'] <= self.filters['volatility']['max']:
            reasons.append(f"Healthy volatility: {tech_data['volatility']:.1%}")
        
        return reasons

    async def _analyze_with_news(self, symbol: str, technical_data: Dict) -> Dict:
        """Combine technical and news analysis"""
        # Get news analysis
        news_data = await self.news_analyzer.analyze_stock_news(symbol)
        
        # Adjust technical scores based on news
        if news_data['has_significant_news']:
            # Get momentum and sentiment
            momentum = technical_data['technical_data']['momentum']
            sentiment = news_data['sentiment_score']
            
            # If both momentum and sentiment agree, boost the signal
            if (momentum > 0 and sentiment > 0) or (momentum < 0 and sentiment < 0):
                # Add news confirmation to reasons
                technical_data['reasons'].append(
                    f"News sentiment ({sentiment:.2f}) confirms {momentum:.1%} momentum"
                )
            
            # Add news-based reasons
            technical_data['reasons'].append(
                f"News Analysis: {self.news_analyzer.get_news_summary(news_data)}"
            )
            
            # Add recent headlines
            headlines = [news['title'] for news in news_data['recent_news'][:3]]
            technical_data['reasons'].extend([f"Recent: {h}" for h in headlines])
        
        technical_data['news_data'] = news_data
        return technical_data