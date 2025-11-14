"""
Cache Manager - Handles all caching operations
"""
import pickle
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages caching of screened stock results
    """
    
    def __init__(self, cache_dir: str, duration_hours: int = 24):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory to store cache files
            duration_hours: How long cache is valid (in hours)
        """
        self.cache_dir = Path(cache_dir)
        self.duration_hours = duration_hours
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Cache manager initialized: {self.cache_dir}")
    
    def _get_cache_file_path(self, market: str) -> Path:
        """Get cache file path for a specific market"""
        return self.cache_dir / f"screened_stocks_{market.lower()}.pkl"
    
    def load(self, market: str) -> Optional[List[str]]:
        """
        Load cached tickers for a market
        
        Args:
            market: Market name (e.g., 'US', 'INDIA')
            
        Returns:
            List of tickers or None if cache is invalid/missing
        """
        cache_file = self._get_cache_file_path(market)
        
        if not cache_file.exists():
            logger.debug(f"No cache file found for {market}")
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Validate cache structure
            if not self._is_valid_cache_structure(cache_data):
                logger.warning(f"Invalid cache structure for {market}")
                return None
            
            # Check if cache is still valid
            if self._is_cache_expired(cache_data['timestamp']):
                logger.info(f"Cache expired for {market}")
                return None
            
            tickers = cache_data.get('tickers', [])
            age_hours = self._get_cache_age_hours(cache_data['timestamp'])
            
            logger.info(f"✓ Loaded {len(tickers)} tickers from cache for {market} (age: {age_hours:.1f}h)")
            
            return tickers
            
        except Exception as e:
            logger.error(f"Error loading cache for {market}: {e}")
            return None
    
    def save(self, market: str, tickers: List[str], metadata: Dict[str, Any] = None):
        """
        Save tickers to cache
        
        Args:
            market: Market name
            tickers: List of tickers to cache
            metadata: Additional metadata to store
        """
        cache_file = self._get_cache_file_path(market)
        
        cache_data = {
            'timestamp': datetime.now(),
            'market': market,
            'tickers': tickers,
            'count': len(tickers),
            'metadata': metadata or {}
        }
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            logger.info(f"✓ Cached {len(tickers)} tickers for {market}")
            
        except Exception as e:
            logger.error(f"Error saving cache for {market}: {e}")
    
    def clear(self, market: Optional[str] = None):
        """
        Clear cache for a specific market or all markets
        
        Args:
            market: Market name or None to clear all
        """
        if market:
            cache_file = self._get_cache_file_path(market)
            if cache_file.exists():
                cache_file.unlink()
                logger.info(f"Cleared cache for {market}")
        else:
            # Clear all cache files
            for cache_file in self.cache_dir.glob("screened_stocks_*.pkl"):
                cache_file.unlink()
            logger.info("Cleared all cache files")
    
    def get_cache_info(self, market: str) -> Optional[Dict[str, Any]]:
        """
        Get information about cached data
        
        Args:
            market: Market name
            
        Returns:
            Dictionary with cache info or None
        """
        cache_file = self._get_cache_file_path(market)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            age_hours = self._get_cache_age_hours(cache_data['timestamp'])
            is_valid = not self._is_cache_expired(cache_data['timestamp'])
            
            return {
                'market': market,
                'timestamp': cache_data['timestamp'],
                'age_hours': age_hours,
                'is_valid': is_valid,
                'ticker_count': cache_data.get('count', 0),
                'file_size_kb': cache_file.stat().st_size / 1024
            }
            
        except Exception as e:
            logger.error(f"Error getting cache info for {market}: {e}")
            return None
    
    def _is_valid_cache_structure(self, cache_data: Dict) -> bool:
        """Check if cache data has required fields"""
        required_fields = ['timestamp', 'market', 'tickers']
        return all(field in cache_data for field in required_fields)
    
    def _is_cache_expired(self, timestamp: datetime) -> bool:
        """Check if cache has expired"""
        age = datetime.now() - timestamp
        return age > timedelta(hours=self.duration_hours)
    
    def _get_cache_age_hours(self, timestamp: datetime) -> float:
        """Get cache age in hours"""
        age = datetime.now() - timestamp
        return age.total_seconds() / 3600
