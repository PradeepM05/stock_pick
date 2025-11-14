"""
India Market Screener
"""
from typing import List, Optional
import logging
from .base_screener import BaseScreener
from ..data.api_client import NSEIndiaClient, YahooFinanceClient, YFinanceScreenerClient

logger = logging.getLogger(__name__)


class IndiaScreener(BaseScreener):
    """Screener for Indian stock market"""
    
    def __init__(self, filters: dict = None, cache_manager=None, api_key: Optional[str] = None):
        """
        Initialize India screener
        
        Args:
            filters: Filtering criteria
            cache_manager: Cache manager instance
            api_key: Yahoo Finance API key (optional)
        """
        self.api_key = api_key
        self.nse_client = NSEIndiaClient()
        self.yahoo_client = YahooFinanceClient(api_key) if api_key else None
        self.yfinance_fallback = YFinanceScreenerClient()  # NEW: Free fallback
        
        super().__init__(filters, cache_manager)
    
    def get_market_name(self) -> str:
        """Return market identifier"""
        return 'INDIA'
    
    def screen_stocks(self, use_cache: bool = True) -> List[str]:
        """
        Screen Indian stocks
        
        Args:
            use_cache: Whether to use cached results
            
        Returns:
            List of Indian stock tickers (with .NS suffix)
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
        
        # Try primary source (NSE India)
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
            logger.error("All data sources failed for India market")
        
        return tickers
    
    def _fetch_from_primary_source(self) -> List[str]:
        """
        Fetch from NSE India (primary source)
        
        Returns:
            List of tickers with .NS suffix
        """
        try:
            logger.info("Using NSE India (primary)...")
            
            # Check if specific indices are requested
            indices = self.filters.get('indices_to_scan', [])
            
            if indices:
                # Fetch from specific indices
                all_tickers = []
                for index in indices:
                    tickers = self.nse_client.fetch_index(index)
                    if tickers:
                        all_tickers.extend(tickers)
                        logger.info(f"  {index}: {len(tickers)} stocks")
                
                if all_tickers:
                    # Remove duplicates
                    all_tickers = list(set(all_tickers))
                    self._log_results(all_tickers, "NSE Indices")
                    return all_tickers
            else:
                # Default to Nifty 500
                tickers = self.nse_client.fetch_nifty_500()
                if tickers:
                    self._log_results(tickers, "NSE Nifty 500")
                    return tickers
                
        except Exception as e:
            logger.error(f"Primary source error: {e}")
        
        return []
    
    def _fetch_from_secondary_source(self) -> List[str]:
        """
        Fetch from yfinance fallback (free method)
        
        Returns:
            List of tickers with .NS suffix
        """
        try:
            logger.info("Using yfinance fallback for India...")
            tickers = self.yfinance_fallback.screen_india_stocks(self.filters)
            
            if tickers:
                # Ensure .NS suffix
                tickers = [t if t.endswith('.NS') else f"{t}.NS" for t in tickers]
                self._log_results(tickers, "YFinance Fallback (India)")
                return tickers
                
        except Exception as e:
            logger.error(f"Fallback source error: {e}")
        
        return []
    
    def _apply_filters(self, tickers: List[str]) -> List[str]:
        """
        Apply India-specific post-fetch filters
        
        Args:
            tickers: Raw ticker list
            
        Returns:
            Filtered ticker list
        """
        # Remove duplicates
        tickers = list(set(tickers))
        
        # Ensure all tickers have .NS suffix
        tickers = [t if t.endswith('.NS') else f"{t}.NS" for t in tickers]
        
        # Filter by exchange if specified
        exchanges = self.filters.get('exchanges', ['NSE', 'BSE'])
        if 'NSE' in exchanges and 'BSE' not in exchanges:
            # Keep only NSE stocks (.NS suffix)
            tickers = [t for t in tickers if t.endswith('.NS')]
        elif 'BSE' in exchanges and 'NSE' not in exchanges:
            # Convert to BSE (.BO suffix)
            tickers = [t.replace('.NS', '.BO') for t in tickers]
        
        logger.info(f"Applied filters: {len(tickers)} stocks remaining")
        return tickers
    
    def fetch_from_multiple_indices(self) -> List[str]:
        """
        Fetch stocks from multiple NSE indices
        
        Returns:
            Combined list of unique tickers
        """
        indices = self.filters.get('indices_to_scan', ['NIFTY500'])
        all_tickers = []
        
        for index in indices:
            try:
                tickers = self.nse_client.fetch_index(index)
                if tickers:
                    all_tickers.extend(tickers)
                    logger.info(f"✓ {index}: {len(tickers)} stocks")
            except Exception as e:
                logger.error(f"Error fetching {index}: {e}")
        
        # Remove duplicates
        return list(set(all_tickers))
    
    def get_exchange_list(self) -> List[str]:
        """Get list of Indian exchanges"""
        return ['NSE', 'BSE']
