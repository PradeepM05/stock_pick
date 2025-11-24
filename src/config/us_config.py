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
    # Market Cap - Quality-focused range
    'market_cap_min': 500_000_000,        # $500M (higher minimum for quality)
    'market_cap_max': 50_000_000_000,     # $50B (avoid mega-caps, focus on growth)
    
    # Liquidity - Ensure tradeable
    'volume_min': 200_000,                # Higher volume for US market liquidity
    
    # Value - Quality-first requirements
    'peg_ratio_max': 1.5,                 # More selective PEG (was 2.0)
    'pe_ratio_max_fallback': 22,          # Lower P/E for US (was 25)
    'pe_ratio_min': 1,                    # Must be profitable
    'roe_min': 12,                        # Higher ROE requirement (was 8)
    
    # Financial Health - Tighter for US market
    'debt_to_equity_max': 1.5,            # Stricter debt (was 2.0)
    'current_ratio_min': 1.0,             # Better liquidity (was 0.8)
    'profit_margin_min': 5,               # Higher margins (was 2)
    
    # Growth - Quality growth requirements
    'revenue_growth_min': 0,              # At least stable (was -10)
    'earnings_growth_min': -5,            # Minor decline allowed (was -10)
    
    # Price Action - Value focus maintained
    'price_above_200ma': False,
    'price_above_50ma': False,
    
    # Quality filters
    'operating_margin_min': 8,            # Higher than India (was 5)
    
    # *** NEW: US-SPECIFIC QUALITY-FIRST CONTROLS ***
    'quality_threshold': 75,              # Higher bar for US stocks
    'min_portfolio_size': 25,             # Larger US portfolios
    'max_portfolio_size': 45,             # More opportunities in US
    
    # US-specific sector considerations
    'us_sector_attractiveness': {
        'Technology': 0.95,               # Slight discount (overvalued)
        'Healthcare': 1.05,               # Defensive premium
        'Industrials': 1.10,              # Infrastructure/reshoring
        'Energy': 1.15,                   # Undervalued sector
        'Financial Services': 1.00,       # Neutral (no concentration issue)
        'Consumer Cyclical': 0.95,        # Economic uncertainty
        'Basic Materials': 1.10,          # Commodity cycle
        'Utilities': 1.05,                # Interest rate beneficiary
        'Real Estate': 0.90,              # Rate sensitivity
        'Communication Services': 0.95    # Mature sector
    },
    
    # Exchange filters
    'exchanges': ['NYSE', 'NASDAQ'],
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