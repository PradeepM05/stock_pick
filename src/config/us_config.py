"""
US Market Configuration
"""
import os


# =============================================================================
# US MARKET DATA SOURCES
# =============================================================================
US_DATA_SOURCES = {
    'primary': 'yfinance_screener',
    'secondary': 'finviz',
    'tertiary': 'financial_modeling_prep'
}


# =============================================================================
# US MARKET FILTERS
# =============================================================================
US_FILTERS = {
    # Market Cap - very wide range to include everything
    'market_cap_min': 50_000_000,        # $50M (very small cap OK)
    'market_cap_max': 5_000_000_000_000, # $5T (all mega caps included)
    
    # Liquidity - minimal requirement
    'volume_min': 50_000,                # Lower threshold
    
    # Fundamentals - very lenient, just basic quality checks
    'pe_ratio_max': 200,                 # Very high (allow any growth stocks)
    'roe_min': 0,                        # Any positive ROE
    'debt_to_equity_max': 10.0,          # Very lenient on debt
    'revenue_growth_min': -50,           # Even declining revenue OK (just not bankrupt)
    'earnings_growth_min': -50,          # Even declining earnings OK
    
    # Price Action - don't filter on technicals
    'price_above_200ma': False,
    'price_above_50ma': False,
    
    # Additional Quality Filters - minimal
    'operating_margin_min': -100,        # Even negative margins OK
    'current_ratio_min': 0.1,            # Very minimal liquidity requirement
    
    # Sector Diversification - include all
    'sectors_include': [],
    'sectors_exclude': [],               # No exclusions!
    
    # Country filters
    'countries': ['US']
}


# =============================================================================
# US VALUATION THRESHOLDS
# =============================================================================
US_VALUATION_THRESHOLDS = {
    'eps_growth_excellent': 15,
    'eps_growth_good': 10,
    'eps_growth_3y_excellent': 12,
    'eps_growth_3y_good': 8,
    'roe_excellent': 20,
    'roe_good': 15,
    'debt_equity_excellent': 0.5,
    'debt_equity_good': 1.0,
}


# =============================================================================
# US MARKET SETTINGS
# =============================================================================
US_MARKET_CONFIG = {
    'market_name': 'US',
    'market_index': 'SPY',
    'currency': 'USD',
    'exchanges': ['NYSE', 'NASDAQ'],
    'trading_hours': {
        'open': '09:30',
        'close': '16:00',
        'timezone': 'America/New_York'
    }
}


# =============================================================================
# US FALLBACK EXCHANGES
# =============================================================================
US_FALLBACK_EXCHANGES = ['NYSE', 'NASDAQ']


# =============================================================================
# OUTPUT FILE
# =============================================================================
US_OUTPUT_FILE = 'stock_picks_us.csv'
