"""
Base Settings - Shared configuration across all markets
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
CACHE_DIR = PROJECT_ROOT / "cache"

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)


# =============================================================================
# ACTION THRESHOLDS - Applied to both markets
# =============================================================================
ACTION_THRESHOLDS = {
    'STRONG_BUY': {
        'composite_min': 75,
        'description': 'High conviction - Best opportunities',
        'needs_deep_analysis': True
    },
    'BUY': {
        'composite_min': 65,
        'description': 'Good opportunity - Quality stocks',
        'needs_deep_analysis': True
    },
    'SPECULATIVE': {
        'composite_min': 50,
        'description': 'Speculative - High risk, high potential',
        'needs_deep_analysis': False
    }
}


# =============================================================================
# VALUATION WEIGHTS - Shared scoring system
# =============================================================================
VALUATION_WEIGHTS = {
    'eps_growth_yoy': 25,
    'eps_growth_3y': 15,
    'roe': 20,
    'debt_equity': 15,
    'pe_vs_sector': 10,
    'peg_ratio': 10,
    'fcf_yield': 5
}


# =============================================================================
# SECTOR BENCHMARKS - For relative scoring
# =============================================================================
SECTOR_BENCHMARKS = {
    'Technology': {
        'typical_pe': 30,
        'typical_roe': 20,
        'typical_debt_equity': 0.5,
        'typical_profit_margin': 20,
        'growth_focused': True,
        'weights': {
            'growth': 0.40,  # Emphasize growth
            'profitability': 0.35,
            'valuation': 0.25
        }
    },
    'Financial Services': {
        'typical_pe': 12,
        'typical_roe': 12,
        'typical_debt_equity': 5.0,  # Banks have high leverage naturally
        'typical_profit_margin': 25,
        'growth_focused': False,
        'weights': {
            'growth': 0.20,
            'profitability': 0.50,  # Emphasize profitability
            'valuation': 0.30
        }
    },
    'Healthcare': {
        'typical_pe': 25,
        'typical_roe': 15,
        'typical_debt_equity': 0.8,
        'typical_profit_margin': 15,
        'growth_focused': True,
        'weights': {
            'growth': 0.35,
            'profitability': 0.35,
            'valuation': 0.30
        }
    },
    'Consumer Cyclical': {
        'typical_pe': 20,
        'typical_roe': 15,
        'typical_debt_equity': 1.2,
        'typical_profit_margin': 8,
        'growth_focused': False,
        'weights': {
            'growth': 0.30,
            'profitability': 0.35,
            'valuation': 0.35
        }
    },
    'Consumer Defensive': {
        'typical_pe': 22,
        'typical_roe': 18,
        'typical_debt_equity': 1.0,
        'typical_profit_margin': 10,
        'growth_focused': False,
        'weights': {
            'growth': 0.25,
            'profitability': 0.40,
            'valuation': 0.35
        }
    },
    'Industrials': {
        'typical_pe': 18,
        'typical_roe': 12,
        'typical_debt_equity': 1.5,
        'typical_profit_margin': 8,
        'growth_focused': False,
        'weights': {
            'growth': 0.30,
            'profitability': 0.35,
            'valuation': 0.35
        }
    },
    'Energy': {
        'typical_pe': 15,
        'typical_roe': 10,
        'typical_debt_equity': 1.0,
        'typical_profit_margin': 5,
        'growth_focused': False,
        'weights': {
            'growth': 0.25,
            'profitability': 0.35,
            'valuation': 0.40  # Emphasize value
        }
    },
    'Utilities': {
        'typical_pe': 18,
        'typical_roe': 8,
        'typical_debt_equity': 2.5,  # Utilities have high leverage
        'typical_profit_margin': 12,
        'growth_focused': False,
        'weights': {
            'growth': 0.15,
            'profitability': 0.35,
            'valuation': 0.50  # Very value-focused
        }
    },
    'Real Estate': {
        'typical_pe': 30,
        'typical_roe': 6,
        'typical_debt_equity': 3.0,  # REITs have high leverage
        'typical_profit_margin': 25,
        'growth_focused': False,
        'weights': {
            'growth': 0.20,
            'profitability': 0.30,
            'valuation': 0.50
        }
    },
    'Communication Services': {
        'typical_pe': 20,
        'typical_roe': 12,
        'typical_debt_equity': 1.5,
        'typical_profit_margin': 15,
        'growth_focused': True,
        'weights': {
            'growth': 0.35,
            'profitability': 0.35,
            'valuation': 0.30
        }
    },
    'Basic Materials': {
        'typical_pe': 15,
        'typical_roe': 10,
        'typical_debt_equity': 1.2,
        'typical_profit_margin': 10,
        'growth_focused': False,
        'weights': {
            'growth': 0.25,
            'profitability': 0.35,
            'valuation': 0.40
        }
    },
    # Default for unknown sectors
    'Default': {
        'typical_pe': 20,
        'typical_roe': 15,
        'typical_debt_equity': 1.0,
        'typical_profit_margin': 10,
        'growth_focused': False,
        'weights': {
            'growth': 0.30,
            'profitability': 0.35,
            'valuation': 0.35
        }
    }
}


# =============================================================================
# API RANKING WEIGHTS
# =============================================================================
API_RANKING_WEIGHTS = {
    'data_freshness': 0.10,
    'data_completeness': 0.15,
    'fundamental_score': 0.45,
    'technical_score': 0.30,
}


# =============================================================================
# CACHE CONFIGURATION
# =============================================================================
CACHE_CONFIG = {
    'enabled': True,
    'duration_hours': 24,
    'refresh_frequency': 'daily',
}


# =============================================================================
# UNIVERSE BUILDER SETTINGS
# =============================================================================
UNIVERSE_BUILDER = {
    'max_stocks_per_scan': 500,
    'use_progressive_filtering': True,
    'stage_1_filters': ['market_cap', 'volume', 'pe_ratio'],
    'stage_2_filters': ['roe', 'debt_to_equity', 'growth'],
    'stage_3_filters': ['technical', 'momentum'],
}


# =============================================================================
# API RETRY CONFIGURATION
# =============================================================================
API_RETRY_CONFIG = {
    'max_retries': 3,
    'timeout_seconds': 30,
    'backoff_multiplier': 2,
}


# =============================================================================
# OUTPUT SETTINGS
# =============================================================================
TOP_N_STOCKS = 20
OUTPUT_FORMAT = 'csv'  # Options: 'csv', 'json', 'excel'


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'datefmt': '%Y-%m-%d %H:%M:%S'
}
