"""
Base Screener - Abstract class for all stock screeners
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseScreener(ABC):
    """
    Abstract base class for stock screeners
    All market-specific screeners should inherit from this
    """
    
    def __init__(self, filters: Dict = None, cache_manager=None):
        """
        Initialize screener
        
        Args:
            filters: Dictionary of filtering criteria
            cache_manager: CacheManager instance for caching results
        """
        self.filters = filters or {}
        self.cache_manager = cache_manager
        self.market_name = self.get_market_name()
        
        logger.info(f"Initialized {self.market_name} screener")
    
    @abstractmethod
    def get_market_name(self) -> str:
        """Return the market name (e.g., 'US', 'INDIA')"""
        pass
    
    @abstractmethod
    def screen_stocks(self, use_cache: bool = True) -> List[str]:
        """
        Screen stocks based on filters
        
        Args:
            use_cache: Whether to use cached results
            
        Returns:
            List of stock ticker symbols
        """
        pass
    
    @abstractmethod
    def _fetch_from_primary_source(self) -> List[str]:
        """Fetch stocks from primary data source"""
        pass
    
    @abstractmethod
    def _fetch_from_secondary_source(self) -> List[str]:
        """Fetch stocks from secondary/fallback data source"""
        pass
    
    def _load_from_cache(self) -> Optional[List[str]]:
        """
        Load stocks from cache if available and valid
        
        Returns:
            List of tickers or None if cache invalid/missing
        """
        if not self.cache_manager:
            return None
        
        return self.cache_manager.load(self.market_name)
    
    def _save_to_cache(self, tickers: List[str]):
        """
        Save tickers to cache
        
        Args:
            tickers: List of stock tickers to cache
        """
        if self.cache_manager and tickers:
            self.cache_manager.save(self.market_name, tickers)
    
    def _apply_filters(self, tickers: List[str]) -> List[str]:
        """
        Apply post-fetch filters to ticker list
        Can be overridden by child classes for custom filtering
        
        Args:
            tickers: List of tickers to filter
            
        Returns:
            Filtered list of tickers
        """
        # Base implementation - can be extended by child classes
        return list(set(tickers))  # Remove duplicates
    
    def _log_results(self, tickers: List[str], source: str):
        """Log screening results"""
        if tickers:
            logger.info(f"✓ {self.market_name} ({source}): Found {len(tickers)} stocks")
        else:
            logger.warning(f"✗ {self.market_name} ({source}): No stocks found")
    
    def validate_filters(self) -> bool:
        """
        Validate that required filters are present and valid
        
        Returns:
            True if filters are valid
        """
        required_keys = ['market_cap_min', 'volume_min']
        
        for key in required_keys:
            if key not in self.filters:
                logger.warning(f"Missing required filter: {key}")
                return False
        
        return True
