"""
Configuration Package
Exposes all configuration settings
"""

from .settings import (
    ACTION_THRESHOLDS,
    VALUATION_WEIGHTS,
    SECTOR_BENCHMARKS,
    API_RANKING_WEIGHTS,
    CACHE_CONFIG,
    UNIVERSE_BUILDER,
    API_RETRY_CONFIG,
    TOP_N_STOCKS,
    OUTPUT_FORMAT,
    LOGGING_CONFIG,
    OUTPUT_DIR,
    CACHE_DIR,
    PROJECT_ROOT
)

from .us_config import (
    US_DATA_SOURCES,
    US_FILTERS,
    US_VALUATION_THRESHOLDS,
    US_MARKET_CONFIG,
    US_FALLBACK_EXCHANGES,
    US_OUTPUT_FILE
)

from .india_config import (
    INDIA_DATA_SOURCES,
    INDIA_FILTERS,
    INDIA_VALUATION_THRESHOLDS,
    INDIA_MARKET_CONFIG,
    INDIA_FALLBACK_EXCHANGES,
    INDIA_OUTPUT_FILE,
    NSE_CONFIG
)


def get_market_config(market='US'):
    """
    Get market-specific configuration
    
    Args:
        market (str): 'US', 'INDIA', or 'BOTH'
        
    Returns:
        dict: Market configuration
    """
    if market == 'US':
        return {
            'filters': US_FILTERS,
            'data_sources': US_DATA_SOURCES,
            'valuation_thresholds': US_VALUATION_THRESHOLDS,
            'market_config': US_MARKET_CONFIG,
            'fallback_exchanges': US_FALLBACK_EXCHANGES,
            'output_file': US_OUTPUT_FILE
        }
    elif market == 'INDIA':
        return {
            'filters': INDIA_FILTERS,
            'data_sources': INDIA_DATA_SOURCES,
            'valuation_thresholds': INDIA_VALUATION_THRESHOLDS,
            'market_config': INDIA_MARKET_CONFIG,
            'fallback_exchanges': INDIA_FALLBACK_EXCHANGES,
            'output_file': INDIA_OUTPUT_FILE
        }
    elif market == 'BOTH':
        return {
            'filters': {**US_FILTERS, **INDIA_FILTERS},
            'data_sources': {**US_DATA_SOURCES, **INDIA_DATA_SOURCES},
            'valuation_thresholds': {
                'US': US_VALUATION_THRESHOLDS,
                'INDIA': INDIA_VALUATION_THRESHOLDS
            },
            'market_config': {
                'US': US_MARKET_CONFIG,
                'INDIA': INDIA_MARKET_CONFIG
            },
            'fallback_exchanges': {
                'US': US_FALLBACK_EXCHANGES,
                'INDIA': INDIA_FALLBACK_EXCHANGES
            },
            'output_file': 'stock_picks_combined.csv'
        }
    else:
        raise ValueError(f"Unknown market: {market}. Choose 'US', 'INDIA', or 'BOTH'")


__all__ = [
    # Base settings
    'ACTION_THRESHOLDS',
    'VALUATION_WEIGHTS',
    'API_RANKING_WEIGHTS',
    'CACHE_CONFIG',
    'UNIVERSE_BUILDER',
    'API_RETRY_CONFIG',
    'TOP_N_STOCKS',
    'OUTPUT_FORMAT',
    'LOGGING_CONFIG',
    'OUTPUT_DIR',
    'CACHE_DIR',
    'PROJECT_ROOT',
    
    # US config
    'US_DATA_SOURCES',
    'US_FILTERS',
    'US_VALUATION_THRESHOLDS',
    'US_MARKET_CONFIG',
    'US_FALLBACK_EXCHANGES',
    'US_OUTPUT_FILE',
    
    # India config
    'INDIA_DATA_SOURCES',
    'INDIA_FILTERS',
    'INDIA_VALUATION_THRESHOLDS',
    'INDIA_MARKET_CONFIG',
    'INDIA_FALLBACK_EXCHANGES',
    'INDIA_OUTPUT_FILE',
    'NSE_CONFIG',
    
    # Helper function
    'get_market_config'
]
