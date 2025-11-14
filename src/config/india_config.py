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
# INDIA MARKET FILTERS - HIDDEN GEMS FOCUS
# =============================================================================
INDIA_FILTERS = {
    # Market Cap (in INR) - TEMPORARILY RELAXED for debugging
    'market_cap_min': 500_000_000,           # ₹50 Cr ($60M - profitable small companies)
    'market_cap_max': 50_000_000_000_000,    # ₹50 Lakh Cr (very high - temporary)
    
    # Liquidity - Ensure tradeable but not overly popular
    'volume_min': 50_000,                    # Decent volume for liquidity
    
    # Value - Use PEG ratio with fallbacks (relaxed)
    'peg_ratio_max': 2.0,                    # More lenient PEG for testing
    'pe_ratio_max_fallback': 30,             # Fallback P/E when no growth data  
    'pe_ratio_min': 1,                       # Must be profitable (no losses)
    'roe_min': 8,                            # Relaxed ROE for testing
    
    # Financial Health - RELAXED for testing
    'debt_to_equity_max': 3.0,            # More lenient debt
    'current_ratio_min': 0.5,             # Relaxed liquidity  
    'profit_margin_min': 1,               # Lower margin requirement
    
    # Growth - RELAXED for testing
    'revenue_growth_min': -20,            # Allow some decline
    'earnings_growth_min': -20,           # Allow some decline
    
    # Price Action - Simple momentum check
    'price_above_200ma': False,           # Don't require momentum (value focus)
    'price_above_50ma': False,
    
    # Quality filters for hidden gems
    'operating_margin_min': 3,            # Profitable operations (lower than US)
    
    # Sector Diversification - include all
    'sectors_include': [],
    'sectors_exclude': [],               # Keep all sectors but add anti-hype logic
    
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
# INDIA VALUATION THRESHOLDS - PEG-Based System
# =============================================================================
INDIA_VALUATION_THRESHOLDS = {
    # PEG ratio scoring (Price/Earnings to Growth) - NEW!
    'peg_excellent': 0.8,       # PEG < 0.8 = excellent value
    'peg_good': 1.2,           # PEG < 1.2 = good value
    'peg_fair': 1.5,           # PEG < 1.5 = fair value
    
    # Growth scoring (updated for Indian market conditions)
    'eps_growth_excellent': 20,    # Slightly lower than US due to different economy
    'eps_growth_good': 12,
    'eps_growth_3y_excellent': 15,
    'eps_growth_3y_good': 10,
    
    # Quality scoring (adjusted for Indian market)
    'roe_excellent': 18,           # Slightly lower than US
    'roe_good': 12,
    'debt_equity_excellent': 0.7,  # Higher than US (different leverage norms)
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
INDIA_OUTPUT_FILE = 'hidden_gems_india.csv'


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