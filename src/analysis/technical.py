"""
Technical Analysis Module
Analyzes price action, trends, and momentum indicators
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """
    Analyzes technical indicators and price action
    """
    
    def __init__(self):
        """Initialize technical analyzer"""
        pass
    
    def analyze(self, ticker: str, period: str = '1y') -> Optional[Dict[str, Any]]:
        """
        Perform technical analysis on a stock
        
        Args:
            ticker: Stock ticker symbol
            period: Historical data period (e.g., '1y', '6mo', '3mo')
            
        Returns:
            Dictionary with technical metrics or None if analysis fails
        """
        try:
            stock = yf.Ticker(ticker)
            
            # Get historical price data
            hist = stock.history(period=period)
            
            if hist.empty or len(hist) < 50:
                logger.warning(f"Insufficient data for {ticker}")
                return None
            
            current_price = hist['Close'].iloc[-1]
            
            technical = {
                'ticker': ticker,
                'current_price': current_price,
                'timestamp': datetime.now(),
                
                # Moving averages
                'sma_50': self._calculate_sma(hist, 50),
                'sma_200': self._calculate_sma(hist, 200),
                'ema_20': self._calculate_ema(hist, 20),
                
                # Trend indicators
                'price_vs_sma50': self._price_vs_ma(current_price, self._calculate_sma(hist, 50)),
                'price_vs_sma200': self._price_vs_ma(current_price, self._calculate_sma(hist, 200)),
                
                # Momentum indicators
                'rsi': self._calculate_rsi(hist),
                'macd': self._calculate_macd(hist),
                
                # Volatility
                'atr': self._calculate_atr(hist),
                'volatility': self._calculate_volatility(hist),
                
                # Price performance
                'return_1m': self._calculate_return(hist, 21),
                'return_3m': self._calculate_return(hist, 63),
                'return_6m': self._calculate_return(hist, 126),
                'return_ytd': self._calculate_ytd_return(hist),
                
                # Volume analysis
                'avg_volume': hist['Volume'].mean(),
                'volume_trend': self._calculate_volume_trend(hist),
                
                # Support/Resistance
                'support': self._find_support(hist),
                'resistance': self._find_resistance(hist),
                
                # Trend strength
                'trend': self._identify_trend(hist),
                'trend_strength': self._calculate_trend_strength(hist),
            }
            
            return technical
            
        except Exception as e:
            logger.error(f"Error in technical analysis for {ticker}: {e}")
            return None
    
    def _calculate_sma(self, hist: pd.DataFrame, period: int) -> Optional[float]:
        """Calculate Simple Moving Average"""
        try:
            if len(hist) >= period:
                return hist['Close'].rolling(window=period).mean().iloc[-1]
        except Exception as e:
            logger.debug(f"Error calculating SMA: {e}")
        return None
    
    def _calculate_ema(self, hist: pd.DataFrame, period: int) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        try:
            if len(hist) >= period:
                return hist['Close'].ewm(span=period, adjust=False).mean().iloc[-1]
        except Exception as e:
            logger.debug(f"Error calculating EMA: {e}")
        return None
    
    def _price_vs_ma(self, price: float, ma: Optional[float]) -> Optional[float]:
        """Calculate percentage difference between price and moving average"""
        if ma and ma > 0:
            return ((price - ma) / ma) * 100
        return None
    
    def _calculate_rsi(self, hist: pd.DataFrame, period: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index"""
        try:
            if len(hist) < period + 1:
                return None
            
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1]
            
        except Exception as e:
            logger.debug(f"Error calculating RSI: {e}")
            return None
    
    def _calculate_macd(self, hist: pd.DataFrame) -> Optional[Dict[str, float]]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        try:
            if len(hist) < 26:
                return None
            
            ema_12 = hist['Close'].ewm(span=12, adjust=False).mean()
            ema_26 = hist['Close'].ewm(span=26, adjust=False).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            histogram = macd_line - signal_line
            
            return {
                'macd': macd_line.iloc[-1],
                'signal': signal_line.iloc[-1],
                'histogram': histogram.iloc[-1]
            }
            
        except Exception as e:
            logger.debug(f"Error calculating MACD: {e}")
            return None
    
    def _calculate_atr(self, hist: pd.DataFrame, period: int = 14) -> Optional[float]:
        """Calculate Average True Range"""
        try:
            if len(hist) < period + 1:
                return None
            
            high = hist['High']
            low = hist['Low']
            close = hist['Close'].shift(1)
            
            tr1 = high - low
            tr2 = abs(high - close)
            tr3 = abs(low - close)
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()
            
            return atr.iloc[-1]
            
        except Exception as e:
            logger.debug(f"Error calculating ATR: {e}")
            return None
    
    def _calculate_volatility(self, hist: pd.DataFrame, period: int = 30) -> Optional[float]:
        """Calculate historical volatility (annualized)"""
        try:
            if len(hist) < period:
                return None
            
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100  # Annualized percentage
            
            return volatility
            
        except Exception as e:
            logger.debug(f"Error calculating volatility: {e}")
            return None
    
    def _calculate_return(self, hist: pd.DataFrame, days: int) -> Optional[float]:
        """Calculate return over specified number of days"""
        try:
            if len(hist) < days:
                return None
            
            current_price = hist['Close'].iloc[-1]
            past_price = hist['Close'].iloc[-days]
            
            return ((current_price - past_price) / past_price) * 100
            
        except Exception as e:
            logger.debug(f"Error calculating return: {e}")
            return None
    
    def _calculate_ytd_return(self, hist: pd.DataFrame) -> Optional[float]:
        """Calculate year-to-date return"""
        try:
            current_year = datetime.now().year
            ytd_data = hist[hist.index.year == current_year]
            
            if len(ytd_data) < 2:
                return None
            
            start_price = ytd_data['Close'].iloc[0]
            current_price = ytd_data['Close'].iloc[-1]
            
            return ((current_price - start_price) / start_price) * 100
            
        except Exception as e:
            logger.debug(f"Error calculating YTD return: {e}")
            return None
    
    def _calculate_volume_trend(self, hist: pd.DataFrame, period: int = 20) -> Optional[str]:
        """Determine if volume is increasing or decreasing"""
        try:
            if len(hist) < period:
                return None
            
            recent_avg = hist['Volume'].tail(period//2).mean()
            older_avg = hist['Volume'].tail(period).head(period//2).mean()
            
            if recent_avg > older_avg * 1.2:
                return 'increasing'
            elif recent_avg < older_avg * 0.8:
                return 'decreasing'
            else:
                return 'stable'
                
        except Exception as e:
            logger.debug(f"Error calculating volume trend: {e}")
            return None
    
    def _find_support(self, hist: pd.DataFrame, lookback: int = 50) -> Optional[float]:
        """Find support level (simplified)"""
        try:
            if len(hist) < lookback:
                return None
            
            recent_data = hist.tail(lookback)
            return recent_data['Low'].min()
            
        except Exception as e:
            logger.debug(f"Error finding support: {e}")
            return None
    
    def _find_resistance(self, hist: pd.DataFrame, lookback: int = 50) -> Optional[float]:
        """Find resistance level (simplified)"""
        try:
            if len(hist) < lookback:
                return None
            
            recent_data = hist.tail(lookback)
            return recent_data['High'].max()
            
        except Exception as e:
            logger.debug(f"Error finding resistance: {e}")
            return None
    
    def _identify_trend(self, hist: pd.DataFrame) -> str:
        """Identify overall trend direction"""
        try:
            sma_50 = self._calculate_sma(hist, 50)
            sma_200 = self._calculate_sma(hist, 200)
            current_price = hist['Close'].iloc[-1]
            
            if not sma_50 or not sma_200:
                return 'unknown'
            
            # Strong uptrend
            if current_price > sma_50 > sma_200:
                return 'strong_uptrend'
            # Uptrend
            elif current_price > sma_50:
                return 'uptrend'
            # Downtrend
            elif current_price < sma_50 and sma_50 < sma_200:
                return 'downtrend'
            # Sideways
            else:
                return 'sideways'
                
        except Exception as e:
            logger.debug(f"Error identifying trend: {e}")
            return 'unknown'
    
    def _calculate_trend_strength(self, hist: pd.DataFrame) -> Optional[float]:
        """Calculate trend strength (0-100)"""
        try:
            if len(hist) < 50:
                return None
            
            # Use ADX-like calculation (simplified)
            returns = hist['Close'].pct_change().dropna()
            
            # Count consecutive positive/negative days
            positive_days = (returns > 0).sum()
            total_days = len(returns)
            
            strength = (positive_days / total_days) * 100
            
            # Adjust for volatility
            volatility = returns.std()
            if volatility > 0:
                strength = strength * (1 - min(volatility * 10, 0.5))
            
            return min(max(strength, 0), 100)
            
        except Exception as e:
            logger.debug(f"Error calculating trend strength: {e}")
            return None
    
    def get_technical_score(self, technical: Dict) -> float:
        """
        Calculate technical score (0-100)
        
        Args:
            technical: Technical metrics dictionary
            
        Returns:
            Technical score between 0 and 100
        """
        if not technical:
            return 0
        
        score = 0
        max_score = 0
        
        # Trend score (0-30 points)
        trend = technical.get('trend', 'unknown')
        max_score += 30
        if trend == 'strong_uptrend':
            score += 30
        elif trend == 'uptrend':
            score += 20
        elif trend == 'sideways':
            score += 10
        
        # RSI score (0-20 points)
        rsi = technical.get('rsi')
        if rsi is not None:
            max_score += 20
            if 40 <= rsi <= 60:
                score += 20  # Neutral zone
            elif 30 <= rsi < 40 or 60 < rsi <= 70:
                score += 15  # Acceptable
            elif rsi < 30:
                score += 10  # Oversold (potential bounce)
        
        # Price vs MA score (0-25 points)
        price_vs_sma50 = technical.get('price_vs_sma50')
        if price_vs_sma50 is not None:
            max_score += 25
            if price_vs_sma50 > 5:
                score += 25
            elif price_vs_sma50 > 0:
                score += 20
            elif price_vs_sma50 > -5:
                score += 10
        
        # Momentum score (0-25 points)
        return_3m = technical.get('return_3m', 0)
        if return_3m is not None:
            max_score += 25
            if return_3m > 20:
                score += 25
            elif return_3m > 10:
                score += 20
            elif return_3m > 0:
                score += 15
            elif return_3m > -10:
                score += 5
        
        # Calculate percentage score
        if max_score > 0:
            return (score / max_score) * 100
        
        return 0
