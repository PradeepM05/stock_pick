"""
Scoring Module
Combines fundamental and technical analysis to generate stock scores and recommendations
WITH SECTOR-RELATIVE SCORING
"""
from typing import Dict, Optional, List, Tuple
import logging
from .fundamental import FundamentalAnalyzer
from .technical import TechnicalAnalyzer

logger = logging.getLogger(__name__)


class StockScorer:
    """
    Scores stocks based on fundamental and technical analysis
    WITH SECTOR-RELATIVE SCORING for better accuracy
    """
    
    def __init__(self, 
                 valuation_weights: Dict = None,
                 valuation_thresholds: Dict = None,
                 action_thresholds: Dict = None,
                 sector_benchmarks: Dict = None):
        """
        Initialize stock scorer
        
        Args:
            valuation_weights: Weights for different valuation metrics
            valuation_thresholds: Market-specific valuation thresholds
            action_thresholds: Thresholds for action recommendations
            sector_benchmarks: Sector-specific benchmarks for relative scoring
        """
        self.valuation_weights = valuation_weights or self._default_weights()
        self.valuation_thresholds = valuation_thresholds or {}
        self.action_thresholds = action_thresholds or self._default_action_thresholds()
        self.sector_benchmarks = sector_benchmarks or {}
        
        # Initialize analyzers
        self.fundamental_analyzer = FundamentalAnalyzer(valuation_thresholds)
        self.technical_analyzer = TechnicalAnalyzer()
    
    def _default_weights(self) -> Dict:
        """Default valuation weights"""
        return {
            'eps_growth_yoy': 25,
            'eps_growth_3y': 15,
            'roe': 20,
            'debt_equity': 15,
            'pe_vs_sector': 10,
            'peg_ratio': 10,
            'fcf_yield': 5
        }
    
    def _default_action_thresholds(self) -> Dict:
        """Default action thresholds"""
        return {
            'STRONG_BUY': {
                'valuation_min': 80,
                'technical_min': 70,
                'description': 'Ultra high conviction - Best opportunities',
                'needs_deep_analysis': True
            },
            'BUY': {
                'valuation_min': 70,
                'technical_min': 60,
                'description': 'High conviction - Quality stocks with good entry',
                'needs_deep_analysis': True
            },
            'WATCH': {
                'valuation_min': 70,
                'technical_min': 40,
                'technical_max': 60,
                'description': 'Good fundamentals, waiting for better technical setup',
                'needs_deep_analysis': False
            },
            'WAIT': {
                'valuation_min': 70,
                'technical_max': 40,
                'description': 'Great company, wrong time',
                'needs_deep_analysis': False
            }
        }
    
    def score_stock(self, ticker: str) -> Optional[Dict]:
        """
        Complete scoring of a stock WITH SECTOR-RELATIVE SCORING
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with scores and recommendation
        """
        try:
            logger.debug(f"Scoring {ticker}...")
            
            # Perform fundamental analysis
            fundamentals = self.fundamental_analyzer.analyze(ticker)
            if not fundamentals:
                logger.warning(f"Could not analyze fundamentals for {ticker}")
                return None
            
            # Perform technical analysis
            technicals = self.technical_analyzer.analyze(ticker)
            if not technicals:
                logger.warning(f"Could not analyze technicals for {ticker}")
                return None
            
            # Get sector for relative scoring
            sector = fundamentals.get('sector', 'Unknown')
            
            # Calculate scores WITH SECTOR-RELATIVE LOGIC
            valuation_score = self._calculate_valuation_score_sector_relative(fundamentals, sector)
            fundamental_quality_score = self._calculate_quality_score_sector_relative(fundamentals, sector)
            technical_score = self.technical_analyzer.get_technical_score(technicals)
            
            # Calculate composite score WITH SECTOR-SPECIFIC WEIGHTS
            composite_score = self._calculate_composite_score(
                valuation_score, 
                fundamental_quality_score, 
                technical_score,
                sector
            )
            
            # Determine action based on composite score
            action = self._determine_action(composite_score)
            
            # Create result
            result = {
                'ticker': ticker,
                'company_name': fundamentals.get('company_name', ticker),
                'sector': sector,
                'industry': fundamentals.get('industry', 'Unknown'),
                
                # Scores
                'valuation_score': round(valuation_score, 2),
                'fundamental_score': round(fundamental_quality_score, 2),
                'technical_score': round(technical_score, 2),
                'composite_score': round(composite_score, 2),
                
                # Action
                'action': action['action'],
                'description': action['description'],
                'needs_deep_analysis': action['needs_deep_analysis'],
                
                # Key metrics for quick reference
                'current_price': technicals.get('current_price'),
                'market_cap': fundamentals.get('market_cap'),
                'pe_ratio': fundamentals.get('pe_ratio'),
                'roe': fundamentals.get('roe'),
                'debt_to_equity': fundamentals.get('debt_to_equity'),
                'earnings_growth': fundamentals.get('earnings_growth'),
                'trend': technicals.get('trend'),
                'rsi': technicals.get('rsi'),
                
                # Full analysis data
                'fundamentals': fundamentals,
                'technicals': technicals
            }
            
            logger.info(f"✓ {ticker}: {action['action']} (V:{valuation_score:.0f} T:{technical_score:.0f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error scoring {ticker}: {e}")
            return None
    
    def _calculate_valuation_score(self, fundamentals: Dict) -> float:
        """
        Calculate weighted valuation score (0-100)
        
        Args:
            fundamentals: Fundamental metrics dictionary
            
        Returns:
            Valuation score between 0 and 100
        """
        total_score = 0
        total_weight = 0
        
        # EPS Growth YoY
        eps_growth = fundamentals.get('eps_growth_yoy') or fundamentals.get('earnings_growth', 0)
        if eps_growth is not None:
            weight = self.valuation_weights.get('eps_growth_yoy', 25)
            score = self._score_eps_growth(eps_growth)
            total_score += score * weight
            total_weight += weight
        
        # ROE
        roe = fundamentals.get('roe', 0)
        if roe is not None:
            weight = self.valuation_weights.get('roe', 20)
            score = self._score_roe(roe)
            total_score += score * weight
            total_weight += weight
        
        # Debt to Equity
        de_ratio = fundamentals.get('debt_to_equity')
        if de_ratio is not None:
            weight = self.valuation_weights.get('debt_equity', 15)
            score = self._score_debt_to_equity(de_ratio)
            total_score += score * weight
            total_weight += weight
        
        # P/E Ratio
        pe_ratio = fundamentals.get('pe_ratio')
        if pe_ratio is not None and pe_ratio > 0:
            weight = self.valuation_weights.get('pe_vs_sector', 10)
            score = self._score_pe_ratio(pe_ratio)
            total_score += score * weight
            total_weight += weight
        
        # PEG Ratio
        peg_ratio = fundamentals.get('peg_ratio')
        if peg_ratio is not None and peg_ratio > 0:
            weight = self.valuation_weights.get('peg_ratio', 10)
            score = self._score_peg_ratio(peg_ratio)
            total_score += score * weight
            total_weight += weight
        
        # FCF Yield
        fcf_yield = fundamentals.get('fcf_yield')
        if fcf_yield is not None:
            weight = self.valuation_weights.get('fcf_yield', 5)
            score = self._score_fcf_yield(fcf_yield)
            total_score += score * weight
            total_weight += weight
        
        # Calculate weighted average
        if total_weight > 0:
            return (total_score / total_weight) * 100
        
        return 0
    
    def _score_eps_growth(self, growth: float) -> float:
        """Score EPS growth (0-1)"""
        excellent = self.valuation_thresholds.get('eps_growth_excellent', 15)
        good = self.valuation_thresholds.get('eps_growth_good', 10)
        
        if growth >= excellent:
            return 1.0
        elif growth >= good:
            return 0.75
        elif growth >= 5:
            return 0.5
        elif growth >= 0:
            return 0.25
        else:
            return 0
    
    def _score_roe(self, roe: float) -> float:
        """Score ROE (0-1)"""
        excellent = self.valuation_thresholds.get('roe_excellent', 20)
        good = self.valuation_thresholds.get('roe_good', 15)
        
        if roe >= excellent:
            return 1.0
        elif roe >= good:
            return 0.75
        elif roe >= 10:
            return 0.5
        elif roe >= 5:
            return 0.25
        else:
            return 0
    
    def _score_debt_to_equity(self, de_ratio: float) -> float:
        """Score Debt to Equity (0-1, lower is better)"""
        excellent = self.valuation_thresholds.get('debt_equity_excellent', 0.5)
        good = self.valuation_thresholds.get('debt_equity_good', 1.0)
        
        if de_ratio <= excellent:
            return 1.0
        elif de_ratio <= good:
            return 0.75
        elif de_ratio <= 2.0:
            return 0.5
        elif de_ratio <= 3.0:
            return 0.25
        else:
            return 0
    
    def _score_pe_ratio(self, pe_ratio: float) -> float:
        """Score P/E ratio (0-1, moderate is better)"""
        if pe_ratio < 10:
            return 0.75  # Might be undervalued or has issues
        elif pe_ratio <= 20:
            return 1.0  # Good valuation
        elif pe_ratio <= 30:
            return 0.6  # Acceptable
        elif pe_ratio <= 40:
            return 0.3  # Expensive
        else:
            return 0  # Very expensive
    
    def _score_peg_ratio(self, peg_ratio: float) -> float:
        """Score PEG ratio (0-1, lower is better)"""
        if peg_ratio < 0:
            return 0
        elif peg_ratio <= 1.0:
            return 1.0  # Undervalued
        elif peg_ratio <= 1.5:
            return 0.75  # Fair value
        elif peg_ratio <= 2.0:
            return 0.5  # Slightly expensive
        else:
            return 0.25  # Expensive
    
    def _score_fcf_yield(self, fcf_yield: float) -> float:
        """Score Free Cash Flow Yield (0-1, higher is better)"""
        if fcf_yield >= 10:
            return 1.0
        elif fcf_yield >= 7:
            return 0.75
        elif fcf_yield >= 5:
            return 0.5
        elif fcf_yield >= 3:
            return 0.25
        else:
            return 0
    
    def _determine_action(self, composite_score: float) -> Dict:
        """
        Determine recommended action based on composite score
        
        Args:
            composite_score: Composite score (0-100)
            
        Returns:
            Dictionary with action and metadata
        """
        # Simple composite-based thresholds
        if composite_score >= 75:
            action = 'STRONG_BUY'
        elif composite_score >= 65:
            action = 'BUY'
        elif composite_score >= 50:
            action = 'SPECULATIVE'
        else:
            action = 'AVOID'
        
        threshold = self.action_thresholds.get(action, {
            'description': 'Does not meet criteria',
            'needs_deep_analysis': False
        })
        
        return {
            'action': action,
            'description': threshold.get('description', 'No description'),
            'needs_deep_analysis': threshold.get('needs_deep_analysis', False)
        }
    
    def batch_score(self, tickers: List[str], max_workers: int = 5) -> List[Dict]:
        """
        Score multiple stocks (can be parallelized in future)
        
        Args:
            tickers: List of ticker symbols
            max_workers: Maximum parallel workers (not implemented yet)
            
        Returns:
            List of scored stocks
        """
        results = []
        
        for ticker in tickers:
            result = self.score_stock(ticker)
            if result:
                results.append(result)
        
        return results
    
    def filter_by_action(self, scored_stocks: List[Dict], 
                        actions: List[str] = None) -> List[Dict]:
        """
        Filter scored stocks by action
        
        Args:
            scored_stocks: List of scored stock dictionaries
            actions: List of actions to filter by (e.g., ['STRONG_BUY', 'BUY'])
            
        Returns:
            Filtered list of stocks
        """
        if not actions:
            actions = ['STRONG_BUY', 'BUY']
        
        return [stock for stock in scored_stocks if stock['action'] in actions]
    
    def rank_stocks(self, scored_stocks: List[Dict], 
                    by: str = 'composite_score') -> List[Dict]:
        """
        Rank stocks by specified metric
        
        Args:
            scored_stocks: List of scored stock dictionaries
            by: Metric to rank by (e.g., 'composite_score', 'valuation_score')
            
        Returns:
            Sorted list of stocks (highest to lowest)
        """
        return sorted(scored_stocks, key=lambda x: x.get(by, 0), reverse=True)
    
    # =========================================================================
    # SECTOR-RELATIVE SCORING METHODS (NEW!)
    # =========================================================================
    
    def _get_sector_benchmark(self, sector: str) -> Dict:
        """Get benchmark values for a sector"""
        return self.sector_benchmarks.get(sector, self.sector_benchmarks.get('Default', {}))
    
    def _calculate_composite_score(self, valuation: float, quality: float, technical: float, sector: str) -> float:
        """
        Calculate composite score using sector-specific weights
        
        Args:
            valuation: Valuation score
            quality: Quality score  
            technical: Technical score
            sector: Stock sector
            
        Returns:
            Weighted composite score
        """
        benchmark = self._get_sector_benchmark(sector)
        weights = benchmark.get('weights', {'growth': 0.30, 'profitability': 0.35, 'valuation': 0.35})
        
        # Map our scores to sector categories
        # Growth = technical (momentum)
        # Profitability = quality (fundamentals)
        # Valuation = valuation (relative value)
        
        composite = (
            valuation * weights.get('valuation', 0.35) +
            quality * weights.get('profitability', 0.35) +
            technical * weights.get('growth', 0.30)
        )
        
        return composite
    
    def _calculate_valuation_score_sector_relative(self, fundamentals: Dict, sector: str) -> float:
        """
        Calculate valuation score RELATIVE to sector benchmarks
        
        This is much more accurate than absolute scoring!
        """
        benchmark = self._get_sector_benchmark(sector)
        
        score = 0
        max_score = 0
        
        # P/E ratio (sector-relative)
        pe = fundamentals.get('pe_ratio')
        typical_pe = benchmark.get('typical_pe', 20)
        if pe is not None and pe > 0:
            max_score += 25
            # Score based on how it compares to sector average
            pe_ratio = pe / typical_pe
            if pe_ratio < 0.8:  # 20% below sector average
                score += 25
            elif pe_ratio < 1.0:  # Below sector average
                score += 20
            elif pe_ratio < 1.2:  # Near sector average
                score += 15
            elif pe_ratio < 1.5:  # Slightly above
                score += 10
            else:  # Way above sector
                score += 5
        
        # ROE (sector-relative)
        roe = fundamentals.get('roe')
        typical_roe = benchmark.get('typical_roe', 15)
        if roe is not None and roe >= 0:  # Added >= 0 check
            max_score += 25
            roe_ratio = roe / typical_roe if typical_roe > 0 else 0
            if roe_ratio > 1.5:  # 50% above sector
                score += 25
            elif roe_ratio > 1.2:  # 20% above sector
                score += 20
            elif roe_ratio > 0.8:  # Near sector average
                score += 15
            elif roe_ratio > 0.5:  # Below but acceptable
                score += 10
            else:
                score += 5
        
        # Debt to Equity (sector-relative)
        de = fundamentals.get('debt_to_equity')
        typical_de = benchmark.get('typical_debt_equity', 1.0)
        if de is not None:
            max_score += 20
            # Lower is better, but relative to sector
            if de < typical_de * 0.5:  # Much lower than sector
                score += 20
            elif de < typical_de * 0.8:  # Lower than sector
                score += 16
            elif de < typical_de * 1.2:  # Near sector average
                score += 12
            elif de < typical_de * 2.0:  # Higher but manageable
                score += 8
            else:  # Way above sector
                score += 4
        
        # Growth (more important for growth sectors)
        earnings_growth = fundamentals.get('earnings_growth')
        if earnings_growth is not None:  # Removed default 0
            max_score += 20
            is_growth_sector = benchmark.get('growth_focused', False)
            if is_growth_sector:
                # Growth sectors: emphasize growth
                if earnings_growth > 20:
                    score += 20
                elif earnings_growth > 15:
                    score += 16
                elif earnings_growth > 10:
                    score += 12
                elif earnings_growth > 5:
                    score += 8
                else:
                    score += 4
            else:
                # Value sectors: don't penalize low growth as much
                if earnings_growth > 15:
                    score += 20
                elif earnings_growth > 10:
                    score += 16
                elif earnings_growth > 5:
                    score += 14
                elif earnings_growth > 0:
                    score += 12
                else:
                    score += 8
        
        # Profit margin (sector-relative)
        margin = fundamentals.get('profit_margin')
        typical_margin = benchmark.get('typical_profit_margin', 10)
        if margin is not None and typical_margin > 0:  # Added None check
            max_score += 10
            margin_ratio = margin / typical_margin
            if margin_ratio > 1.5:
                score += 10
            elif margin_ratio > 1.0:
                score += 8
            elif margin_ratio > 0.7:
                score += 6
            else:
                score += 4
        
        # Calculate percentage
        if max_score > 0:
            return (score / max_score) * 100
        
        return 50  # Default middle score if no data
    
    def _calculate_quality_score_sector_relative(self, fundamentals: Dict, sector: str) -> float:
        """
        Calculate fundamental quality score RELATIVE to sector
        
        Different sectors have different quality characteristics
        """
        benchmark = self._get_sector_benchmark(sector)
        
        score = 0
        max_score = 0
        
        # Profitability (adjusted for sector)
        profit_margin = fundamentals.get('profit_margin')
        typical_margin = benchmark.get('typical_profit_margin', 10)
        if profit_margin is not None:  # Removed default 0
            max_score += 30
            if profit_margin > typical_margin * 1.3:
                score += 30
            elif profit_margin > typical_margin:
                score += 24
            elif profit_margin > typical_margin * 0.7:
                score += 18
            elif profit_margin > 0:
                score += 12
            else:
                score += 6
        
        # ROE (adjusted for sector)
        roe = fundamentals.get('roe')
        typical_roe = benchmark.get('typical_roe', 15)
        if roe is not None:  # Removed default 0
            max_score += 30
            if roe > typical_roe * 1.5:
                score += 30
            elif roe > typical_roe:
                score += 24
            elif roe > typical_roe * 0.7:
                score += 18
            elif roe > 0:
                score += 12
        
        # Financial stability (adjusted for sector)
        de = fundamentals.get('debt_to_equity')
        typical_de = benchmark.get('typical_debt_equity', 1.0)
        current_ratio = fundamentals.get('current_ratio')
        
        if de is not None:
            max_score += 20
            # For sectors that naturally have high debt (banks, utilities, REITs)
            # don't penalize as much
            if de < typical_de:
                score += 20
            elif de < typical_de * 1.5:
                score += 16
            elif de < typical_de * 2.0:
                score += 12
            else:
                score += 8
        
        if current_ratio is not None and current_ratio > 0:  # Added None check
            max_score += 20
            if current_ratio > 2.0:
                score += 20
            elif current_ratio > 1.5:
                score += 16
            elif current_ratio > 1.0:
                score += 12
            else:
                score += 8
        
        if max_score > 0:
            return (score / max_score) * 100
        
        return 50  # Default
