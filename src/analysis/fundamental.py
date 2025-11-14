"""
Fundamental Analysis Module
Analyzes company fundamentals including EPS growth, ROE, debt ratios, etc.
"""
import yfinance as yf
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """
    Analyzes fundamental metrics of stocks
    """
    
    def __init__(self, valuation_thresholds: Dict = None):
        """
        Initialize fundamental analyzer
        
        Args:
            valuation_thresholds: Thresholds for scoring (market-specific)
        """
        self.thresholds = valuation_thresholds or {}
    
    def analyze(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Perform fundamental analysis on a stock
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with fundamental metrics or None if analysis fails
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info:
                logger.warning(f"No data available for {ticker}")
                return None
            
            fundamentals = {
                'ticker': ticker,
                'company_name': info.get('longName', ticker),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                
                # Valuation metrics
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'peg_ratio': info.get('pegRatio'),
                'price_to_book': info.get('priceToBook'),
                'price_to_sales': info.get('priceToSalesTrailing12Months'),
                
                # Profitability metrics
                'roe': info.get('returnOnEquity'),
                'roa': info.get('returnOnAssets'),
                'profit_margin': info.get('profitMargins'),
                'operating_margin': info.get('operatingMargins'),
                
                # Growth metrics
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_growth': info.get('earningsGrowth'),
                'earnings_quarterly_growth': info.get('earningsQuarterlyGrowth'),
                
                # Financial health
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'quick_ratio': info.get('quickRatio'),
                
                # Cash flow
                'free_cash_flow': info.get('freeCashflow'),
                'operating_cash_flow': info.get('operatingCashflow'),
                
                # EPS metrics
                'eps_trailing': info.get('trailingEps'),
                'eps_forward': info.get('forwardEps'),
                
                # Dividend
                'dividend_yield': info.get('dividendYield'),
                'payout_ratio': info.get('payoutRatio'),
                
                # Trading metrics
                'volume': info.get('volume'),
                'avg_volume': info.get('averageVolume'),
                'beta': info.get('beta'),
            }
            
            # Calculate derived metrics
            fundamentals['fcf_yield'] = self._calculate_fcf_yield(fundamentals)
            fundamentals['eps_growth_yoy'] = self._calculate_eps_growth(stock)
            
            # Convert percentages to actual percentages (multiply by 100)
            for key in ['roe', 'roa', 'profit_margin', 'operating_margin', 
                       'revenue_growth', 'earnings_growth', 'dividend_yield']:
                if fundamentals.get(key) is not None:
                    fundamentals[key] = fundamentals[key] * 100
            
            return fundamentals
            
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
            return None
    
    def _calculate_fcf_yield(self, fundamentals: Dict) -> Optional[float]:
        """Calculate Free Cash Flow Yield"""
        fcf = fundamentals.get('free_cash_flow')
        market_cap = fundamentals.get('market_cap')
        
        if fcf and market_cap and market_cap > 0:
            return (fcf / market_cap) * 100
        
        return None
    
    def _calculate_eps_growth(self, stock) -> Optional[float]:
        """Calculate year-over-year EPS growth"""
        try:
            # Get historical EPS data
            earnings = stock.get_earnings_history()
            
            if earnings is not None and len(earnings) >= 2:
                # Get last two annual EPS values
                current_eps = earnings.iloc[-1].get('epsActual')
                previous_eps = earnings.iloc[-2].get('epsActual')
                
                if current_eps and previous_eps and previous_eps != 0:
                    growth = ((current_eps - previous_eps) / abs(previous_eps)) * 100
                    return growth
                    
        except Exception as e:
            logger.debug(f"Could not calculate EPS growth: {e}")
        
        return None
    
    def is_fundamentally_strong(self, fundamentals: Dict) -> bool:
        """
        Quick check if stock has strong fundamentals
        
        Args:
            fundamentals: Fundamental metrics dictionary
            
        Returns:
            True if fundamentals are strong
        """
        if not fundamentals:
            return False
        
        # Basic quality checks
        checks = [
            fundamentals.get('market_cap', 0) > 0,
            fundamentals.get('roe', 0) > self.thresholds.get('roe_good', 12),
            fundamentals.get('debt_to_equity', float('inf')) < self.thresholds.get('debt_equity_good', 2.0),
            fundamentals.get('current_ratio', 0) > 1.0,
            fundamentals.get('earnings_growth', 0) > 0
        ]
        
        # At least 4 out of 5 checks should pass
        return sum(checks) >= 4
    
    def get_quality_score(self, fundamentals: Dict) -> float:
        """
        Calculate a simple quality score (0-100)
        
        Args:
            fundamentals: Fundamental metrics dictionary
            
        Returns:
            Quality score between 0 and 100
        """
        if not fundamentals:
            return 0
        
        score = 0
        max_score = 0
        
        # ROE score (0-20 points)
        roe = fundamentals.get('roe', 0)
        if roe is not None:
            max_score += 20
            if roe > self.thresholds.get('roe_excellent', 20):
                score += 20
            elif roe > self.thresholds.get('roe_good', 15):
                score += 15
            elif roe > 10:
                score += 10
        
        # Debt score (0-20 points)
        de_ratio = fundamentals.get('debt_to_equity', float('inf'))
        if de_ratio is not None and de_ratio != float('inf'):
            max_score += 20
            if de_ratio < self.thresholds.get('debt_equity_excellent', 0.5):
                score += 20
            elif de_ratio < self.thresholds.get('debt_equity_good', 1.0):
                score += 15
            elif de_ratio < 2.0:
                score += 10
        
        # Growth score (0-20 points)
        earnings_growth = fundamentals.get('earnings_growth', 0)
        if earnings_growth is not None:
            max_score += 20
            if earnings_growth > self.thresholds.get('eps_growth_excellent', 15):
                score += 20
            elif earnings_growth > self.thresholds.get('eps_growth_good', 10):
                score += 15
            elif earnings_growth > 5:
                score += 10
        
        # Profitability score (0-20 points)
        profit_margin = fundamentals.get('profit_margin', 0)
        if profit_margin is not None:
            max_score += 20
            if profit_margin > 15:
                score += 20
            elif profit_margin > 10:
                score += 15
            elif profit_margin > 5:
                score += 10
        
        # Valuation score (0-20 points)
        pe_ratio = fundamentals.get('pe_ratio', float('inf'))
        if pe_ratio is not None and pe_ratio != float('inf') and pe_ratio > 0:
            max_score += 20
            if pe_ratio < 15:
                score += 20
            elif pe_ratio < 20:
                score += 15
            elif pe_ratio < 30:
                score += 10
        
        # Calculate percentage score
        if max_score > 0:
            return (score / max_score) * 100
        
        return 0
