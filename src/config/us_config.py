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
# US MARKET FILTERS - HIDDEN GEMS FOCUS
# =============================================================================
US_FILTERS = {
    # Market Cap - TEMPORARILY RELAXED for testing (will find some results)
    'market_cap_min': 100_000_000,        # $100M (profitable small companies)
    'market_cap_max': 100_000_000_000,    # $100B (include some large caps for testing)
    
    # Liquidity - Ensure tradeable but not overly popular
    'volume_min': 100_000,                # Decent volume for liquidity
    
    # Value - Use PEG ratio with smart fallbacks
    'peg_ratio_max': 2.0,                 # More lenient PEG for testing
    'pe_ratio_max_fallback': 25,          # Fallback P/E when no growth data
    'pe_ratio_min': 1,                    # Must be profitable (no losses)
    'roe_min': 8,                         # Relaxed ROE for testing
    
    # Financial Health - RELAXED for testing
    'debt_to_equity_max': 2.0,            # More lenient debt
    'current_ratio_min': 0.8,             # Relaxed liquidity
    'profit_margin_min': 2,               # Lower margin requirement
    
    # Growth - RELAXED for testing  
    'revenue_growth_min': -10,            # Allow some decline
    'earnings_growth_min': -10,           # Allow some decline
    
    # Price Action - Simple momentum check
    'price_above_200ma': False,           # Don't require momentum (value focus)
    'price_above_50ma': False,
    
    # Quality filters for hidden gems
    'operating_margin_min': 5,            # Profitable operations
    
    # Avoid hype sectors (can be enabled if desired)
    'sectors_include': [],
    'sectors_exclude': [],               # Keep all sectors but add anti-hype logic
    
    # Country filters
    'countries': ['US']
}


# =============================================================================
# US VALUATION THRESHOLDS
# =============================================================================
US_VALUATION_THRESHOLDS = {
    # PEG ratio scoring (Price/Earnings to Growth) - NEW!
    'peg_excellent': 0.8,       # PEG < 0.8 = excellent value
    'peg_good': 1.2,           # PEG < 1.2 = good value
    'peg_fair': 1.5,           # PEG < 1.5 = fair value
    
    # Growth scoring (updated for PEG compatibility)
    'eps_growth_excellent': 25,
    'eps_growth_good': 15,
    'eps_growth_3y_excellent': 20,
    'eps_growth_3y_good': 12,
    
    # Quality scoring (unchanged)
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