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
    
    def __init__(self, max_workers: int = 3, request_delay: float = 0.5):
        """
        Initialize bulk fetcher with conservative rate limiting
        
        Args:
            max_workers: Number of parallel threads (reduced from 10 to 3)
            request_delay: Delay between requests in seconds
        """
        self.max_workers = max_workers
        self.request_delay = request_delay
        self.last_request_time = 0
    
    def fetch_basic_fundamentals(self, tickers: List[str], batch_size: int = 20) -> Dict[str, Dict]:
        """
        Fetch basic fundamentals for multiple tickers with aggressive rate limiting
        
        Args:
            tickers: List of ticker symbols
            batch_size: Number of tickers to process in each batch (reduced from 50)
            
        Returns:
            Dictionary mapping ticker to basic fundamentals
        """
        logger.info(f"Fetching basic fundamentals for {len(tickers)} stocks...")
        logger.info("Using conservative rate limiting to avoid API throttling...")
        
        results = {}
        failed = []
        
        # Process in smaller batches with longer delays
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(tickers) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} stocks)...")
            
            batch_results = self._fetch_batch_with_retries(batch)
            results.update(batch_results)
            
            # Count successful vs failed
            batch_failed = [t for t in batch if t not in batch_results]
            failed.extend(batch_failed)
            
            success_rate = len(batch_results) / len(batch) * 100 if batch else 0
            logger.info(f"  Batch {batch_num}: {len(batch_results)} successful, {len(batch_failed)} failed ({success_rate:.1f}%)")
            
            # Adaptive delay between batches based on success rate
            if i + batch_size < len(tickers):
                if success_rate < 50:
                    delay = 5.0  # Long delay if many failures
                    logger.warning(f"High failure rate, increasing delay to {delay}s")
                elif success_rate < 80:
                    delay = 3.0  # Medium delay if moderate failures
                else:
                    delay = 2.0  # Standard delay if mostly successful
                
                logger.info(f"  Waiting {delay}s before next batch...")
                time.sleep(delay)
        
        success_rate = len(results) / len(tickers) * 100 if tickers else 0
        logger.info(f"\nTotal: {len(results)} stocks fetched, {len(failed)} failed ({success_rate:.1f}% success)")
        
        # Emergency fallback if too many failures
        if success_rate < 20 and len(results) < 10:
            logger.error(f"Critical: Very low success rate ({success_rate:.1f}%)")
            logger.error("Attempting emergency single-threaded fallback...")
            
            emergency_results = self._emergency_fallback(failed[:30])  # Try 30 most important
            results.update(emergency_results)
            
            final_success_rate = len(results) / len(tickers) * 100 if tickers else 0
            logger.info(f"After emergency fallback: {len(results)} stocks ({final_success_rate:.1f}% success)")
        
        # If success rate is still too low, suggest remedial action
        if success_rate < 30:
            logger.error(f"Low success rate ({success_rate:.1f}%) indicates severe API throttling")
            logger.error("Consider:")
            logger.error("  1. Getting Yahoo Finance API key")
            logger.error("  2. Reducing batch sizes further")
            logger.error("  3. Increasing delays between requests")
            logger.error("  4. Running during off-peak hours")
        
        return results
    
    def _emergency_fallback(self, tickers: List[str]) -> Dict[str, Dict]:
        """Emergency single-threaded fallback with maximum delays"""
        logger.info("Using emergency single-threaded mode...")
        results = {}
        
        for i, ticker in enumerate(tickers):
            if i > 0 and i % 5 == 0:
                logger.info(f"  Emergency progress: {i}/{len(tickers)}")
            
            # Very long delays between requests
            if i > 0:
                time.sleep(2.0)
            
            try:
                data = self._fetch_single(ticker)
                if data:
                    results[ticker] = data
            except:
                continue
        
        return results
    
    def _fetch_batch_with_retries(self, tickers: List[str], max_retries: int = 2) -> Dict[str, Dict]:
        """Fetch a batch of tickers with retry logic"""
        results = {}
        failed_tickers = tickers.copy()
        
        for retry_count in range(max_retries + 1):
            if not failed_tickers:
                break
                
            if retry_count > 0:
                delay = 2 ** retry_count  # Exponential backoff
                logger.info(f"  Retry {retry_count}/{max_retries} with {delay}s delay...")
                time.sleep(delay)
            
            # Reduce concurrency on retries
            workers = max(1, self.max_workers // (retry_count + 1))
            
            batch_results = self._fetch_batch(failed_tickers, workers)
            results.update(batch_results)
            
            # Update failed list
            failed_tickers = [t for t in failed_tickers if t not in batch_results]
            
            if batch_results:
                logger.debug(f"    Retry {retry_count}: {len(batch_results)} recovered")
        
        return results
    
    def _fetch_batch(self, tickers: List[str], workers: int = None) -> Dict[str, Dict]:
        """Fetch a batch of tickers in parallel with controlled concurrency"""
        results = {}
        workers = workers or self.max_workers
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all tasks
            future_to_ticker = {
                executor.submit(self._fetch_single_with_delay, ticker): ticker 
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
    
    def _fetch_single_with_delay(self, ticker: str) -> Optional[Dict]:
        """Fetch single ticker with rate limiting"""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        
        return self._fetch_single(ticker)
    
    def _fetch_single(self, ticker: str) -> Optional[Dict]:
        """
        Fetch basic fundamentals for a single ticker with enhanced error handling
        
        Returns only essential screening data to minimize API calls
        """
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                if not info or len(info) < 5:
                    if attempt < max_retries - 1:
                        time.sleep(0.5)
                        continue
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
                    'peg_ratio': info.get('pegRatio'),  # NEW: PEG ratio from yfinance
                    
                    # Profitability
                    'roe': info.get('returnOnEquity'),
                    'profit_margin': info.get('profitMargins'),
                    'operating_margin': info.get('operatingMargins'),
                    
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
                for key in ['roe', 'profit_margin', 'operating_margin', 'revenue_growth', 'earnings_growth']:
                    if basic_data.get(key) is not None:
                        basic_data[key] = basic_data[key] * 100
                
                # Calculate PEG manually if not provided
                if not basic_data.get('peg_ratio'):
                    pe = basic_data.get('pe_ratio')
                    earnings_growth = basic_data.get('earnings_growth')
                    if pe and earnings_growth and earnings_growth > 0:
                        basic_data['peg_ratio'] = pe / earnings_growth
                
                return basic_data
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Handle rate limiting specifically
                if ('rate limit' in error_str or 
                    'too many requests' in error_str or 
                    '401' in error_str or
                    'unauthorized' in error_str):
                    
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter for rate limits
                        delay = (1.5 ** attempt) + (ticker.__hash__() % 10) / 10
                        time.sleep(delay)
                        continue
                    else:
                        logger.debug(f"Rate limited: {ticker}")
                        return None
                
                # Handle other errors
                else:
                    if attempt < max_retries - 1:
                        time.sleep(0.2)
                        continue
                    else:
                        logger.debug(f"Error fetching {ticker}: {e}")
                        return None
        
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
        
        logger.info(f"\n[OK] {len(passed)} stocks passed filters")
        logger.info(f"[X] {len(stocks_data) - len(passed)} stocks filtered out:")
        
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
        
        # PEG ratio (Price/Earnings to Growth) - WITH FALLBACKS
        peg = data.get('peg_ratio')
        pe = data.get('pe_ratio')
        earnings_growth = data.get('earnings_growth')

        # Convert to float if string (yfinance sometimes returns strings)
        try:
            peg = float(peg) if peg is not None and peg != '' else None
        except (ValueError, TypeError):
            peg = None

        try:
            pe = float(pe) if pe is not None and pe != '' else None
        except (ValueError, TypeError):
            pe = None

        try:
            earnings_growth = float(earnings_growth) if earnings_growth is not None and earnings_growth != '' else None
        except (ValueError, TypeError):
            earnings_growth = None

        # Try to use PEG if available
        if peg is not None and peg > 0:
            if peg > filters.get('peg_ratio_max', float('inf')):
                return 'peg_too_high'
        # Fallback: If no PEG, calculate it manually
        elif pe and earnings_growth and pe > 0 and earnings_growth > 0:
            calculated_peg = pe / earnings_growth
            if calculated_peg > filters.get('peg_ratio_max', float('inf')):
                return 'calculated_peg_too_high'
        # Final fallback: Use P/E only (more lenient)
        elif pe and pe > 0:
            # If no growth data, use relaxed P/E limit
            pe_max_fallback = filters.get('pe_ratio_max_fallback', 25)  # More lenient than PEG
            if pe > pe_max_fallback:
                return 'pe_too_high_fallback'

        # P/E ratio (keep for minimum profitability check)
        if pe is not None:
            if pe < filters.get('pe_ratio_min', 0):  # Must be profitable
                return 'negative_or_low_earnings'
        
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
        
        # Profit margin filter for quality
        profit_margin = data.get('profit_margin')
        if profit_margin is not None and profit_margin < filters.get('profit_margin_min', 0):
            return 'profit_margin_too_low'
        
        # Operating margin filter for quality
        operating_margin = data.get('operating_margin')
        if operating_margin is not None and operating_margin < filters.get('operating_margin_min', 0):
            return 'operating_margin_too_low'
        
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
    
    def find_simple_gems(self, stocks_data: Dict[str, Dict], max_results: int = 10) -> List[str]:
        """
        Simple method to find hidden gems from filtered stocks
        
        Args:
            stocks_data: Dictionary of ticker -> fundamentals
            max_results: Maximum gems to return
            
        Returns:
            List of ticker symbols ranked by simple gem score
        """
        logger.info(f"\n💎 Finding hidden gems from {len(stocks_data)} stocks...")
        
        gem_candidates = []
        
        for ticker, data in stocks_data.items():
            score = self._simple_gem_score(data)
            if score > 5:  # Only consider stocks with decent scores
                gem_candidates.append((ticker, score, data))
        
        # Sort by score (highest first)
        gem_candidates.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Found {len(gem_candidates)} potential gems")
        if gem_candidates:
            logger.info(f"Best gem score: {gem_candidates[0][1]:.1f} ({gem_candidates[0][0]})")
        
        # Return just the tickers
        return [ticker for ticker, score, data in gem_candidates[:max_results]]
    
    def _simple_gem_score(self, data: Dict) -> float:
        """
        Calculate simple gem score (0-10)
        Higher is better
        """
        score = 0
        
        # PEG ratio points (much smarter than just P/E!)
        peg = data.get('peg_ratio')
        if peg and peg > 0:
            if peg < 0.8:
                score += 4    # Excellent value (undervalued growth)
            elif peg < 1.2:
                score += 3    # Good value
            elif peg < 1.5:
                score += 2    # Fair value
            elif peg < 2.0:
                score += 1    # Acceptable
        
        # Backup: P/E points (if PEG not available)
        elif not peg:
            pe = data.get('pe_ratio')
            if pe and 0 < pe < 8:
                score += 3
            elif pe and 8 <= pe < 12:
                score += 2
            elif pe and 12 <= pe < 15:
                score += 1
        
        # Quality points (high ROE)
        roe = data.get('roe')
        if roe and roe > 20:
            score += 3
        elif roe and roe > 15:
            score += 2
        elif roe and roe > 10:
            score += 1
        
        # Growth points
        rev_growth = data.get('revenue_growth')
        if rev_growth and rev_growth > 10:
            score += 2
        elif rev_growth and rev_growth > 0:
            score += 1
        
        # Safety points (low debt)
        debt_equity = data.get('debt_to_equity')
        if debt_equity is not None and debt_equity < 0.5:
            score += 2
        elif debt_equity is not None and debt_equity < 1.0:
            score += 1
        
        # Size bonus (prefer smaller companies)
        market_cap = data.get('market_cap', 0)
        if market_cap < 500_000_000:  # < $500M
            score += 0.5
        
        return score