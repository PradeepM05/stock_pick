"""
Bulk Fetcher - Efficiently fetch basic fundamentals for multiple stocks
"""
import yfinance as yf
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logger = logging.getLogger(__name__)


class BulkFetcher:
    """
    Efficiently fetch basic fundamentals for multiple stocks
    """
    
    def __init__(self, max_workers: int = 10):
        """
        Initialize bulk fetcher
        
        Args:
            max_workers: Number of parallel threads for fetching
        """
        self.max_workers = max_workers
    
    def fetch_basic_fundamentals(self, tickers: List[str], batch_size: int = 50) -> Dict[str, Dict]:
        """
        Fetch basic fundamentals for multiple tickers in parallel
        
        Args:
            tickers: List of ticker symbols
            batch_size: Number of tickers to process in each batch
            
        Returns:
            Dictionary mapping ticker to basic fundamentals
        """
        logger.info(f"Fetching basic fundamentals for {len(tickers)} stocks...")
        
        results = {}
        failed = []
        
        # Process in batches
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(tickers) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} stocks)...")
            
            batch_results = self._fetch_batch(batch)
            results.update(batch_results)
            
            # Count successful vs failed
            batch_failed = [t for t in batch if t not in batch_results]
            failed.extend(batch_failed)
            
            logger.info(f"  Batch {batch_num}: {len(batch_results)} successful, {len(batch_failed)} failed")
            
            # Brief pause between batches to avoid rate limiting
            if i + batch_size < len(tickers):
                time.sleep(1)
        
        logger.info(f"\nTotal: {len(results)} stocks fetched, {len(failed)} failed")
        
        return results
    
    def _fetch_batch(self, tickers: List[str]) -> Dict[str, Dict]:
        """Fetch a batch of tickers in parallel"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_ticker = {
                executor.submit(self._fetch_single, ticker): ticker 
                for ticker in tickers
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    data = future.result()
                    if data:
                        results[ticker] = data
                except Exception as e:
                    logger.debug(f"Failed to fetch {ticker}: {e}")
        
        return results
    
    def _fetch_single(self, ticker: str) -> Optional[Dict]:
        """
        Fetch basic fundamentals for a single ticker
        
        Returns only essential screening data to minimize API calls
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info or len(info) < 5:
                return None
            
            # Extract only essential screening metrics
            basic_data = {
                'ticker': ticker,
                'name': info.get('longName', ticker),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                
                # Key filtering metrics
                'market_cap': info.get('marketCap', 0),
                'volume': info.get('volume', 0),
                'avg_volume': info.get('averageVolume', 0),
                
                # Valuation metrics
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                
                # Profitability
                'roe': info.get('returnOnEquity'),
                'profit_margin': info.get('profitMargins'),
                
                # Growth
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_growth': info.get('earningsGrowth'),
                
                # Financial health
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                
                # Price
                'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
            }
            
            # Convert percentages to actual percentages
            for key in ['roe', 'profit_margin', 'revenue_growth', 'earnings_growth']:
                if basic_data.get(key) is not None:
                    basic_data[key] = basic_data[key] * 100
            
            return basic_data
            
        except Exception as e:
            logger.debug(f"Error fetching {ticker}: {e}")
            return None
    
    def apply_filters(self, stocks_data: Dict[str, Dict], filters: Dict) -> List[str]:
        """
        Apply screening filters to bulk fetched data
        
        Args:
            stocks_data: Dictionary of ticker -> basic fundamentals
            filters: Filter criteria dictionary
            
        Returns:
            List of tickers that pass all filters
        """
        logger.info(f"\nApplying filters to {len(stocks_data)} stocks...")
        logger.info("Filter criteria:")
        for key, value in filters.items():
            if key not in ['sectors_include', 'sectors_exclude', 'countries', 'exchanges']:
                logger.info(f"  {key}: {value}")
        
        passed = []
        failed_reasons = {}
        
        for ticker, data in stocks_data.items():
            reason = self._check_filters(data, filters)
            
            if reason is None:
                passed.append(ticker)
            else:
                failed_reasons[reason] = failed_reasons.get(reason, 0) + 1
        
        logger.info(f"\n✓ {len(passed)} stocks passed filters")
        logger.info(f"✗ {len(stocks_data) - len(passed)} stocks filtered out:")
        
        for reason, count in sorted(failed_reasons.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  - {reason}: {count} stocks")
        
        return passed
    
    def _check_filters(self, data: Dict, filters: Dict) -> Optional[str]:
        """
        Check if a stock passes all filters
        
        Returns:
            None if passes, or reason string if fails
        """
        # Market cap
        market_cap = data.get('market_cap', 0)
        if market_cap < filters.get('market_cap_min', 0):
            return 'market_cap_too_low'
        if market_cap > filters.get('market_cap_max', float('inf')):
            return 'market_cap_too_high'
        
        # Volume
        volume = data.get('avg_volume') or data.get('volume', 0)
        if volume < filters.get('volume_min', 0):
            return 'volume_too_low'
        
        # P/E ratio
        pe = data.get('pe_ratio')
        if pe is not None:
            if pe > filters.get('pe_ratio_max', float('inf')):
                return 'pe_too_high'
            if pe < 0:  # Negative P/E (losing money)
                return 'negative_earnings'
        
        # ROE
        roe = data.get('roe')
        if roe is not None and roe < filters.get('roe_min', 0):
            return 'roe_too_low'
        
        # Debt to Equity
        de = data.get('debt_to_equity')
        if de is not None and de > filters.get('debt_to_equity_max', float('inf')):
            return 'debt_too_high'
        
        # Revenue growth
        rev_growth = data.get('revenue_growth')
        if rev_growth is not None and rev_growth < filters.get('revenue_growth_min', 0):
            return 'revenue_growth_too_low'
        
        # Earnings growth
        earn_growth = data.get('earnings_growth')
        if earn_growth is not None and earn_growth < filters.get('earnings_growth_min', 0):
            return 'earnings_growth_too_low'
        
        # Current ratio
        current_ratio = data.get('current_ratio')
        if current_ratio is not None and current_ratio < filters.get('current_ratio_min', 0):
            return 'current_ratio_too_low'
        
        # Sector exclusions
        sector = data.get('sector', '')
        sectors_exclude = filters.get('sectors_exclude', [])
        if sector in sectors_exclude:
            return f'sector_excluded_{sector}'
        
        # Sector inclusions (if specified)
        sectors_include = filters.get('sectors_include', [])
        if sectors_include and sector not in sectors_include:
            return 'sector_not_included'
        
        # Passed all filters
        return None
