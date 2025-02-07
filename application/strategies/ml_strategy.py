from datetime import datetime
from decimal import Decimal
from typing import Optional
import logging
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier  # Changed from Regressor to Classifier
from sklearn.preprocessing import StandardScaler
from ..strategies.strategy_interface import TradingStrategy
from trading_platform.domain.models.instrument import Instrument, Signal
from trading_platform.config import Config

logger = logging.getLogger(__name__)

class MLTradingStrategy(TradingStrategy):
    def __init__(self, config: Config):
        self.config = config
        self.model = RandomForestClassifier(  # Changed to Classifier
            n_estimators=100,
            max_depth=5,
            min_samples_split=5,
            min_samples_leaf=4,
            random_state=42
        )
        self.scaler = StandardScaler()

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_volatility(self, prices: pd.Series, window: int = 20) -> float:
        returns = np.log(prices / prices.shift(1))
        return returns.std() * np.sqrt(252)  # Annualized volatility

    def _calculate_market_condition(self, df: pd.DataFrame) -> float:
        # Calculate various market condition indicators
        recent_volatility = self._calculate_volatility(df['Close'][-20:])
        rsi = self._calculate_rsi(df['Close']).iloc[-1]
        
        # Penalize high volatility and extreme RSI values
        volatility_penalty = max(0, recent_volatility - 0.2) * 0.5
        rsi_penalty = min(abs(rsi - 50) / 50, 1) * 0.3
        
        return 1 - (volatility_penalty + rsi_penalty)

    async def analyze(self,
                     market_data: pd.DataFrame,
                     instrument: Instrument) -> Optional[Signal]:
        try:
            df = market_data.copy()
            
            # Calculate technical indicators
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['RSI'] = self._calculate_rsi(df['Close'])
            df['Volatility'] = df['Close'].rolling(window=20).apply(
                lambda x: np.log(x / x.shift(1)).std() * np.sqrt(252)
            )
            
            # Calculate price momentum
            df['Returns'] = df['Close'].pct_change()
            df['Momentum'] = df['Returns'].rolling(window=10).mean()
            
            # Prepare features
            features = [
                'Close', 'Volume', 'SMA_20', 'SMA_50', 'RSI', 
                'Volatility', 'Momentum'
            ]
            
            # Ensure we have enough data
            df = df.dropna()
            if len(df) < 50:
                logger.warning(f"Insufficient data for {instrument.symbol}")
                return None
            
            X = df[features].values[:-1]
            y = (df['Close'].shift(-1) > df['Close']).values[:-1]
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model and predict
            self.model.fit(X_scaled, y)
            
            # Get current features
            current_features = df[features].values[-1:]
            current_features_scaled = self.scaler.transform(current_features)
            
            # Get prediction and feature importances
            prediction = self.model.predict_proba(current_features_scaled)[0][1]  # Now works with Classifier
            feature_importance = dict(zip(features, self.model.feature_importances_))
            
            # Calculate market condition adjustment
            market_condition = self._calculate_market_condition(df)
            adjusted_confidence = prediction * market_condition
            
            logger.info(f"Raw prediction: {prediction:.2%}")
            logger.info(f"Market condition: {market_condition:.2%}")
            logger.info(f"Adjusted confidence: {adjusted_confidence:.2%}")
            
            # Only generate signal if confidence exceeds threshold after adjustments
            if adjusted_confidence > self.config.min_prediction_confidence:
                current_price = Decimal(str(df['Close'].iloc[-1]))
                
                # Check trend direction
                trend = "positive" if df['SMA_20'].iloc[-1] > df['SMA_50'].iloc[-1] else "negative"
                vol_state = "high" if df['Volatility'].iloc[-1] > 0.2 else "normal"
                
                signal = Signal(
                    instrument=instrument,
                    type='BUY',
                    confidence=float(adjusted_confidence),
                    timestamp=datetime.now(),
                    price=current_price,
                    technical_indicators={
                        'rsi': float(df['RSI'].iloc[-1]),
                        'sma_20': float(df['SMA_20'].iloc[-1]),
                        'sma_50': float(df['SMA_50'].iloc[-1]),
                        'volatility': float(df['Volatility'].iloc[-1]),
                        'momentum': float(df['Momentum'].iloc[-1])
                    },
                    prediction=float(prediction)
                )
                
                # Add detailed reasoning
                signal.reason = [
                    f"ML model prediction: {prediction:.1%}",
                    f"Market condition adjustment: {market_condition:.1%}",
                    f"Current RSI: {df['RSI'].iloc[-1]:.1f}",
                    f"Volatility: {df['Volatility'].iloc[-1]:.2f} ({vol_state})",
                    f"10-day Momentum: {df['Momentum'].iloc[-1]:.2%}",
                    f"Trend: {trend} (SMA20 vs SMA50)"
                ]
                
                return signal
            
            return None

        except Exception as e:
            logger.error(f"Error in ML strategy: {str(e)}")
            logger.exception("Detailed error:")  # Add traceback for debugging
            return None