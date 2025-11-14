"""
US Market Screener
"""
from typing import List, Optional
import logging
from .base_screener import BaseScreener
from ..data.api_client import YahooFinanceClient, YFinanceScreenerClient

logger = logging.getLogger(__name__)


class USScreener(BaseScreener):
    """Screener for US stock market"""
    
    def __init__(self, filters: dict = None, cache_manager=None, api_key: Optional[str] = None):
        """
        Initialize US screener
        
        Args:
            filters: Filtering criteria
            cache_manager: Cache manager instance
            api_key: Yahoo Finance API key
        """
        self.api_key = api_key
        self.yahoo_client = YahooFinanceClient(api_key)
        self.yfinance_fallback = YFinanceScreenerClient()
        
        super().__init__(filters, cache_manager)
    
    def get_market_name(self) -> str:
        """Return market identifier"""
        return 'US'
    
    def screen_stocks(self, use_cache: bool = True) -> List[str]:
        """
        Screen US stocks
        
        Args:
            use_cache: Whether to use cached results
            
        Returns:
            List of US stock tickers
        """
        # Try loading from cache first
        if use_cache:
            cached = self._load_from_cache()
            if cached:
                return cached
        
        logger.info(f"Screening {self.market_name} stocks...")
        
        # Validate filters
        if not self.validate_filters():
            logger.error("Invalid filters provided")
            return []
        
        # Try primary source (Yahoo API)
        tickers = self._fetch_from_primary_source()
        
        # If primary fails, try secondary source
        if not tickers:
            logger.info("Primary source failed, trying secondary source...")
            tickers = self._fetch_from_secondary_source()
        
        # Apply any post-fetch filters
        if tickers:
            tickers = self._apply_filters(tickers)
            self._save_to_cache(tickers)
            self._log_results(tickers, "combined")
        else:
            logger.error("All data sources failed for US market")
        
        return tickers
    
    def _fetch_from_primary_source(self) -> List[str]:
        """
        Fetch from Yahoo Finance API (primary source)
        
        Returns:
            List of tickers
        """
        try:
            if self.api_key:
                logger.info(f"✅ Yahoo Finance API key detected: {self.api_key[:8]}...")
                logger.info("🔄 Using Yahoo Finance API (primary source)...")
                tickers = self.yahoo_client.screen_stocks(
                    region='US',
                    filters=self.filters,
                    max_results=self.filters.get('max_stocks_per_scan', 5000)  # Increased for more stocks
                )
                
                if tickers:
                    self._log_results(tickers, "Yahoo API")
                    return tickers
                else:
                    logger.warning("⚠️ Yahoo API returned no results, trying fallback...")
            else:
                logger.warning("❌ No Yahoo Finance API key found!")
                logger.info("   Create .env file with: YAHOO_FINANCE_API_KEY=your_key")
                logger.info("   Falling back to free data sources...")
                
        except Exception as e:
            logger.error(f"❌ Yahoo API error: {e}")
            logger.info("🔄 Falling back to free data sources...")
        
        return []
    
    def _fetch_from_secondary_source(self) -> List[str]:
        """
        Fetch from YFinance screener module (fallback)
        
        Returns:
            List of tickers
        """
        try:
            logger.info("Using YFinance screener module (secondary)...")
            tickers = self.yfinance_fallback.screen_us_stocks(self.filters)
            
            if tickers:
                self._log_results(tickers, "YFinance Screener")
                return tickers
                
        except Exception as e:
            logger.error(f"Secondary source error: {e}")
        
        return []
    
    def _apply_filters(self, tickers: List[str]) -> List[str]:
        """
        Apply US-specific post-fetch filters
        
        Args:
            tickers: Raw ticker list
            
        Returns:
            Filtered ticker list
        """
        # Remove duplicates
        tickers = list(set(tickers))
        
        # Filter out non-US exchanges if needed
        # (Most tickers from Yahoo are already US-based)
        
        # Apply sector filters if specified
        sectors_exclude = self.filters.get('sectors_exclude', [])
        if sectors_exclude:
            # Note: This would require fetching sector info for each ticker
            # We can implement this later if needed
            pass
        
        logger.info(f"Applied filters: {len(tickers)} stocks remaining")
        return tickers
    
    def get_exchange_list(self) -> List[str]:
        """Get list of US exchanges"""
        return ['NYSE', 'NASDAQ', 'AMEX']