"""
Helper Functions
Common utility functions used across the application
"""
import os
from typing import Any, Dict, List, Optional
from pathlib import Path
import json


def load_env_vars() -> Dict[str, str]:
    """
    Load environment variables
    
    Returns:
        Dictionary of environment variables
    """
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv not installed, will use system env vars
    
    return {
        'yahoo_api_key': os.getenv('YAHOO_FINANCE_API_KEY'),
        'default_market': os.getenv('DEFAULT_MARKET', 'US'),
        'enable_cache': os.getenv('ENABLE_CACHE', 'true').lower() == 'true',
        'cache_duration': int(os.getenv('CACHE_DURATION_HOURS', '24')),
        'log_level': os.getenv('LOG_LEVEL', 'INFO')
    }


def ensure_directory(path: Path) -> Path:
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        path: Path to directory
        
    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def format_currency(amount: float, currency: str = 'USD') -> str:
    """
    Format amount as currency
    
    Args:
        amount: Amount to format
        currency: Currency code (USD, INR, etc.)
        
    Returns:
        Formatted currency string
    """
    symbols = {
        'USD': '$',
        'INR': '₹',
        'EUR': '€',
        'GBP': '£'
    }
    
    symbol = symbols.get(currency, currency)
    
    if amount >= 1_000_000_000:
        return f"{symbol}{amount/1_000_000_000:.2f}B"
    elif amount >= 1_000_000:
        return f"{symbol}{amount/1_000_000:.2f}M"
    elif amount >= 1_000:
        return f"{symbol}{amount/1_000:.2f}K"
    else:
        return f"{symbol}{amount:.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format value as percentage
    
    Args:
        value: Value to format
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimals}f}%"


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calculate percentage change
    
    Args:
        old_value: Original value
        new_value: New value
        
    Returns:
        Percentage change
    """
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers
    
    Args:
        numerator: Top number
        denominator: Bottom number
        default: Value to return if division fails
        
    Returns:
        Division result or default
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except:
        return default


def chunks(lst: List[Any], n: int) -> List[List[Any]]:
    """
    Split list into chunks of size n
    
    Args:
        lst: List to split
        n: Chunk size
        
    Returns:
        List of chunks
    """
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def merge_dicts(*dicts: Dict) -> Dict:
    """
    Merge multiple dictionaries
    
    Args:
        *dicts: Dictionaries to merge
        
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def save_json(data: Any, filepath: Path) -> bool:
    """
    Save data to JSON file
    
    Args:
        data: Data to save
        filepath: Path to save file
        
    Returns:
        True if successful
    """
    try:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving JSON: {e}")
        return False


def load_json(filepath: Path) -> Optional[Any]:
    """
    Load data from JSON file
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Loaded data or None if failed
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return None


def clean_ticker(ticker: str) -> str:
    """
    Clean and normalize ticker symbol
    
    Args:
        ticker: Raw ticker symbol
        
    Returns:
        Cleaned ticker symbol
    """
    if not ticker:
        return ""
    
    # Remove whitespace
    ticker = ticker.strip().upper()
    
    # Remove any special characters except dots and hyphens
    # (needed for exchanges like .NS, .BO, etc.)
    return ticker


def is_valid_ticker(ticker: str) -> bool:
    """
    Validate ticker symbol format
    
    Args:
        ticker: Ticker symbol to validate
        
    Returns:
        True if valid
    """
    if not ticker or len(ticker) < 1:
        return False
    
    # Basic validation: alphanumeric with dots/hyphens
    return ticker.replace('.', '').replace('-', '').isalnum()


def get_market_from_ticker(ticker: str) -> Optional[str]:
    """
    Determine market from ticker symbol
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Market identifier or None
    """
    if ticker.endswith('.NS') or ticker.endswith('.BO'):
        return 'INDIA'
    elif '.' not in ticker:
        return 'US'
    else:
        return None
