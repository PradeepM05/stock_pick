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
    # Market Cap (in INR) - Focused range for quality
    'market_cap_min': 1_000_000_000,         # ₹100 Cr (higher minimum for quality)
    'market_cap_max': 5_000_000_000_000,     # ₹5 Lakh Cr (reasonable maximum)
    
    # Liquidity - Ensure tradeable
    'volume_min': 100_000,                   # Increased for better liquidity
    
    # Value - Stricter requirements
    'peg_ratio_max': 1.5,                    # More selective PEG (was 2.0)
    'pe_ratio_max_fallback': 25,             # Reduced from 30
    'pe_ratio_min': 1,                       # Must be profitable
    'roe_min': 12,                           # Higher ROE requirement (was 8)
    
    # Financial Health - Tighter requirements
    'debt_to_equity_max': 2.5,               # Reduced from 3.0
    'current_ratio_min': 1.0,                # Increased from 0.5
    'profit_margin_min': 3,                  # Maintained
    
    # Growth - Stable or growing companies
    'revenue_growth_min': 0,                 # At least stable (was -20)
    'earnings_growth_min': -10,              # Allow minor decline (was -20)
    
    # Price Action - Simple momentum check
    'price_above_200ma': False,
    'price_above_50ma': False,
    
    # Quality filters
    'operating_margin_min': 5,               # Higher requirement (was 3)
    
    # *** NEW: SECTOR DIVERSIFICATION CONTROLS ***
    'max_sector_allocation': 0.25,           # Max 25% per sector
    'max_financial_services': 5,             # Max 5 bank stocks out of 20
    'min_sectors_required': 5,               # Must have at least 5 sectors
    
    # Bank-specific stricter filters
    'bank_specific_filters': {
        'min_roe': 15,                       # Higher ROE for banks
        'max_pe': 12,                        # Lower P/E for banks  
        'min_technical_score': 75            # Require strong technicals
    },
    
    # Sector caps
    'sector_caps': {
        'Financial Services': 5,             # Max 5 bank stocks
        'Technology': 5,
        'Healthcare': 4,
        'Industrials': 4,
        'Consumer Cyclical': 3,
        'Energy': 2
    },
    
    # Exchange and index settings
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