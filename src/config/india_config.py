"""
India Market Configuration
"""
import os


# =============================================================================
# INDIA MARKET DATA SOURCES
# =============================================================================
INDIA_DATA_SOURCES = {
    'primary': 'nse_india',
    'secondary': 'bse_api',
    'tertiary': 'screener_in'
}


# =============================================================================
# INDIA MARKET FILTERS
# =============================================================================
INDIA_FILTERS = {
    # Market Cap (in INR) - very wide range
    'market_cap_min': 50_000_000,        # ₹50 Cr (very small cap OK)
    'market_cap_max': 50_000_000_000_000, # ₹50,00,000 Cr (~$6T - unlimited basically)
    
    # Liquidity - minimal
    'volume_min': 10_000,                # Very low threshold
    
    # Fundamentals - very lenient
    'pe_ratio_max': 200,                 # Very high (allow any growth stocks)
    'roe_min': 0,                        # Any positive ROE
    'debt_to_equity_max': 10.0,          # Very lenient on debt
    'revenue_growth_min': -50,           # Even declining OK
    'earnings_growth_min': -50,          # Even declining OK
    
    # Price Action
    'price_above_200ma': False,
    'price_above_50ma': False,
    
    # Additional Filters - minimal
    'operating_margin_min': -100,        # Even negative OK
    'current_ratio_min': 0.1,            # Very minimal
    
    # Sector Diversification - include all
    'sectors_include': [],
    'sectors_exclude': [],               # No exclusions!
    
    # Specific to India
    'exchanges': ['NSE', 'BSE'],
    'indices_to_scan': [
        'NIFTY500',
        'NIFTY_MIDCAP_100',
        'NIFTY_SMALLCAP_100',
        'NIFTY_MIDSMALLCAP_400'
    ]
}


# =============================================================================
# INDIA VALUATION THRESHOLDS
# =============================================================================
INDIA_VALUATION_THRESHOLDS = {
    'eps_growth_excellent': 12,
    'eps_growth_good': 8,
    'eps_growth_3y_excellent': 10,
    'eps_growth_3y_good': 7,
    'roe_excellent': 18,
    'roe_good': 12,
    'debt_equity_excellent': 0.7,
    'debt_equity_good': 1.5,
}


# =============================================================================
# INDIA MARKET SETTINGS
# =============================================================================
INDIA_MARKET_CONFIG = {
    'market_name': 'INDIA',
    'market_index': '^NSEI',  # Nifty 50
    'currency': 'INR',
    'exchanges': ['NSE', 'BSE'],
    'trading_hours': {
        'open': '09:15',
        'close': '15:30',
        'timezone': 'Asia/Kolkata'
    }
}


# =============================================================================
# INDIA FALLBACK EXCHANGES
# =============================================================================
INDIA_FALLBACK_EXCHANGES = ['NSE']


# =============================================================================
# OUTPUT FILE
# =============================================================================
INDIA_OUTPUT_FILE = 'stock_picks_india.csv'


# =============================================================================
# NSE SPECIFIC SETTINGS
# =============================================================================
NSE_CONFIG = {
    'base_url': 'https://nsearchives.nseindia.com',
    'nifty_500_csv': '/content/indices/ind_nifty500list.csv',
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
}
