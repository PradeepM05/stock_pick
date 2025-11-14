"""
Stock Screeners Package
"""

from .base_screener import BaseScreener
from .us_screener import USScreener
from .india_screener import IndiaScreener


def create_screener(market: str, filters: dict = None, 
                   cache_manager=None, api_key: str = None):
    """
    Factory function to create appropriate screener based on market
    
    Args:
        market: Market identifier ('US', 'INDIA')
        filters: Filtering criteria
        cache_manager: Cache manager instance
        api_key: API key for data sources
        
    Returns:
        Screener instance for the specified market
        
    Raises:
        ValueError: If market is not supported
    """
    market = market.upper()
    
    if market == 'US':
        return USScreener(filters=filters, cache_manager=cache_manager, api_key=api_key)
    elif market == 'INDIA':
        return IndiaScreener(filters=filters, cache_manager=cache_manager, api_key=api_key)
    else:
        raise ValueError(f"Unsupported market: {market}. Choose 'US' or 'INDIA'")


__all__ = [
    'BaseScreener',
    'USScreener',
    'IndiaScreener',
    'create_screener'
]
