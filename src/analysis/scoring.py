"""
Scoring Module
Combines fundamental and technical analysis to generate stock scores and recommendations
WITH SECTOR-RELATIVE SCORING AND QUALITY-FIRST DIVERSIFICATION
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
    AND QUALITY-FIRST DIVERSIFICATION to prevent concentration
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
            
            logger.info(f"[OK] {ticker}: {action['action']} (V:{valuation_score:.0f} T:{technical_score:.0f})")
            
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
        
        # Calculate weighted average
        if total_weight > 0:
            return (total_score / total_weight)
        
        return 50  # Default score if no metrics available
    
    def _score_eps_growth(self, eps_growth: float) -> float:
        """Score EPS growth rate (0-100)"""
        if eps_growth >= 25:
            return 100
        elif eps_growth >= 15:
            return 80
        elif eps_growth >= 10:
            return 60
        elif eps_growth >= 5:
            return 40
        elif eps_growth >= 0:
            return 20
        else:
            return 0
    
    def _score_roe(self, roe: float) -> float:
        """Score Return on Equity (0-100)"""
        if roe >= 20:
            return 100
        elif roe >= 15:
            return 80
        elif roe >= 10:
            return 60
        elif roe >= 5:
            return 40
        elif roe >= 0:
            return 20
        else:
            return 0
    
    def _score_debt_to_equity(self, de_ratio: float) -> float:
        """Score Debt to Equity ratio (0-100, lower is better)"""
        if de_ratio <= 0.3:
            return 100
        elif de_ratio <= 0.6:
            return 80
        elif de_ratio <= 1.0:
            return 60
        elif de_ratio <= 1.5:
            return 40
        elif de_ratio <= 2.0:
            return 20
        else:
            return 0
    
    def _score_pe_ratio(self, pe_ratio: float) -> float:
        """Score P/E ratio (0-100)"""
        if pe_ratio <= 10:
            return 100
        elif pe_ratio <= 15:
            return 80
        elif pe_ratio <= 20:
            return 60
        elif pe_ratio <= 25:
            return 40
        elif pe_ratio <= 30:
            return 20
        else:
            return 0
    
    def _score_peg_ratio(self, peg_ratio: float) -> float:
        """Score PEG ratio (0-100)"""
        if peg_ratio <= 0.5:
            return 100
        elif peg_ratio <= 1.0:
            return 80
        elif peg_ratio <= 1.5:
            return 60
        elif peg_ratio <= 2.0:
            return 40
        elif peg_ratio <= 2.5:
            return 20
        else:
            return 0
    
    def _determine_action(self, composite_score: float) -> Dict:
        """
        Determine investment action based on composite score
        
        Args:
            composite_score: Overall score (0-100)
            
        Returns:
            Dictionary with action and description
        """
        if composite_score >= 80:
            return {
                'action': 'STRONG_BUY',
                'description': 'Ultra high conviction - Best opportunities',
                'needs_deep_analysis': True
            }
        elif composite_score >= 70:
            return {
                'action': 'BUY',
                'description': 'High conviction - Quality stocks with good entry',
                'needs_deep_analysis': True
            }
        elif composite_score >= 60:
            return {
                'action': 'WATCH',
                'description': 'Good fundamentals, waiting for better technical setup',
                'needs_deep_analysis': False
            }
        elif composite_score >= 50:
            return {
                'action': 'WAIT',
                'description': 'Great company, wrong time',
                'needs_deep_analysis': False
            }
        else:
            return {
                'action': 'HOLD',
                'description': 'Hold or consider selling',
                'needs_deep_analysis': False
            }
    
    def _get_sector_benchmark(self, sector: str) -> Dict:
        """Get benchmark values for a sector with proper defaults"""
        
        # Default sector benchmarks if none provided
        default_benchmarks = {
            'Technology': {
                'typical_pe': 25,
                'typical_roe': 18,
                'typical_debt_equity': 0.3,
                'typical_profit_margin': 15,
                'growth_focused': True,
                'weights': {'growth': 0.40, 'profitability': 0.30, 'valuation': 0.30}
            },
            'Healthcare': {
                'typical_pe': 20,
                'typical_roe': 15,
                'typical_debt_equity': 0.4,
                'typical_profit_margin': 12,
                'growth_focused': False,
                'weights': {'growth': 0.25, 'profitability': 0.40, 'valuation': 0.35}
            },
            'Financial Services': {
                'typical_pe': 12,
                'typical_roe': 12,
                'typical_debt_equity': 3.0,  # Banks naturally have high leverage
                'typical_profit_margin': 25,
                'growth_focused': False,
                'weights': {'growth': 0.30, 'profitability': 0.45, 'valuation': 0.25}
            },
            'Energy': {
                'typical_pe': 15,
                'typical_roe': 10,
                'typical_debt_equity': 0.8,
                'typical_profit_margin': 8,
                'growth_focused': False,
                'weights': {'growth': 0.25, 'profitability': 0.35, 'valuation': 0.40}
            },
            'Industrials': {
                'typical_pe': 18,
                'typical_roe': 12,
                'typical_debt_equity': 0.6,
                'typical_profit_margin': 10,
                'growth_focused': False,
                'weights': {'growth': 0.30, 'profitability': 0.35, 'valuation': 0.35}
            },
            'Consumer Cyclical': {
                'typical_pe': 16,
                'typical_roe': 14,
                'typical_debt_equity': 0.5,
                'typical_profit_margin': 8,
                'growth_focused': False,
                'weights': {'growth': 0.35, 'profitability': 0.35, 'valuation': 0.30}
            },
            'Consumer Defensive': {
                'typical_pe': 22,
                'typical_roe': 16,
                'typical_debt_equity': 0.4,
                'typical_profit_margin': 12,
                'growth_focused': False,
                'weights': {'growth': 0.20, 'profitability': 0.45, 'valuation': 0.35}
            },
            'Default': {
                'typical_pe': 18,
                'typical_roe': 15,
                'typical_debt_equity': 0.6,
                'typical_profit_margin': 10,
                'growth_focused': False,
                'weights': {'growth': 0.30, 'profitability': 0.35, 'valuation': 0.35}
            }
        }
        
        # Use provided benchmarks if available, otherwise use defaults
        if self.sector_benchmarks:
            return self.sector_benchmarks.get(sector, self.sector_benchmarks.get('Default', default_benchmarks['Default']))
        else:
            return default_benchmarks.get(sector, default_benchmarks['Default'])
    
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

    def apply_quality_diversification(self, stocks: List[Dict], 
                                    min_portfolio_size: int = 25,
                                    max_portfolio_size: int = 40,
                                    quality_threshold: float = 70) -> List[Dict]:
        """
        Quality-first portfolio construction with intelligent diversification
        
        Picks best stocks regardless of arbitrary limits, but applies progressive
        penalties to prevent over-concentration in any sector.
        """
        from collections import defaultdict
        import numpy as np
        
        logger.info(f"Applying quality-first diversification (threshold: {quality_threshold})")
        
        # Step 1: Filter by absolute quality threshold
        quality_stocks = [s for s in stocks if s['composite_score'] >= quality_threshold]
        logger.info(f"Step 1: {len(quality_stocks)} stocks above quality threshold")
        
        if not quality_stocks:
            logger.warning("No stocks meet quality threshold, lowering to 60")
            quality_stocks = [s for s in stocks if s['composite_score'] >= 60]
        
        # Step 2: Calculate sector-relative rankings
        enhanced_stocks = self._calculate_sector_relative_rankings(quality_stocks)
        
        # Step 3: Apply progressive concentration penalties
        penalty_adjusted_stocks = self._apply_concentration_penalties(enhanced_stocks)
        
        # Step 4: Dynamic portfolio sizing based on opportunity landscape
        optimal_size = self._calculate_optimal_portfolio_size(
            penalty_adjusted_stocks, min_portfolio_size, max_portfolio_size
        )
        
        # Step 5: Apply sector attractiveness weighting
        final_stocks = self._apply_sector_attractiveness(penalty_adjusted_stocks)
        
        # Step 6: Final selection
        portfolio = final_stocks[:optimal_size]
        
        # Step 7: Analytics and reporting
        analytics = self.get_portfolio_analytics(portfolio)
        self._log_portfolio_analytics(analytics)
        
        return portfolio
    
    def _calculate_sector_relative_rankings(self, stocks: List[Dict]) -> List[Dict]:
        """Add sector percentile scores to help identify sector leaders"""
        from collections import defaultdict
        
        sector_stocks = defaultdict(list)
        
        # Group by sector
        for stock in stocks:
            sector_stocks[stock['sector']].append(stock)
        
        # Rank within sector and add percentile scores
        enhanced_stocks = []
        for sector, sector_list in sector_stocks.items():
            # Sort by composite score within sector
            sector_list.sort(key=lambda x: x['composite_score'], reverse=True)
            
            for i, stock in enumerate(sector_list):
                # Add sector percentile (0-100, higher is better)
                sector_percentile = ((len(sector_list) - i) / len(sector_list)) * 100
                stock['sector_percentile'] = sector_percentile
                stock['sector_rank'] = i + 1
                
                # Sector leader bonus for top performers
                if sector_percentile >= 80:  # Top 20% in sector
                    stock['sector_leader_bonus'] = 3
                elif sector_percentile >= 60:  # Top 40% in sector  
                    stock['sector_leader_bonus'] = 1
                else:
                    stock['sector_leader_bonus'] = 0
                
                enhanced_stocks.append(stock)
        
        # Add enhanced score
        for stock in enhanced_stocks:
            stock['enhanced_score'] = stock['composite_score'] + stock['sector_leader_bonus']
        
        enhanced_stocks.sort(key=lambda x: x['enhanced_score'], reverse=True)
        return enhanced_stocks
    
    def _apply_concentration_penalties(self, stocks: List[Dict]) -> List[Dict]:
        """Apply progressive penalties for sector concentration"""
        from collections import defaultdict
        
        sector_counts = defaultdict(int)
        penalty_adjusted_stocks = []
        
        # Progressive penalty schedule - gets expensive to over-concentrate
        concentration_penalties = {
            1: 1.00,  # No penalty for first stock in sector
            2: 0.98,  # 2% penalty for second stock
            3: 0.95,  # 5% penalty for third stock  
            4: 0.90,  # 10% penalty for fourth stock
            5: 0.83,  # 17% penalty for fifth stock
            6: 0.75,  # 25% penalty for sixth stock
            7: 0.65,  # 35% penalty for seventh stock
            8: 0.55,  # 45% penalty for eighth+ stocks
        }
        
        for stock in stocks:
            sector = stock['sector']
            sector_counts[sector] += 1
            position_in_sector = sector_counts[sector]
            
            # Apply concentration penalty
            penalty_factor = concentration_penalties.get(
                position_in_sector, 
                concentration_penalties[8]  # Maximum penalty for 8+ stocks
            )
            
            stock['concentration_penalty_pct'] = (1 - penalty_factor) * 100
            stock['penalty_adjusted_score'] = stock['enhanced_score'] * penalty_factor
            stock['position_in_sector'] = position_in_sector
            
            penalty_adjusted_stocks.append(stock)
            
            # Log penalties for transparency
            if penalty_factor < 0.95:
                logger.info(f"📉 {stock['ticker']} ({sector} #{position_in_sector}): "
                          f"{(1-penalty_factor)*100:.0f}% concentration penalty")
        
        # Re-sort by penalty-adjusted score
        penalty_adjusted_stocks.sort(key=lambda x: x['penalty_adjusted_score'], reverse=True)
        return penalty_adjusted_stocks
    
    def _calculate_optimal_portfolio_size(self, stocks: List[Dict], 
                                        min_size: int, max_size: int) -> int:
        """Calculate optimal portfolio size based on opportunity quality"""
        import numpy as np
        
        scores = [s['penalty_adjusted_score'] for s in stocks]
        
        if not scores:
            return min_size
        
        # Count high-quality opportunities
        excellent_count = len([s for s in scores if s >= 85])
        good_count = len([s for s in scores if s >= 75])
        acceptable_count = len([s for s in scores if s >= 65])
        
        # Quality-based sizing logic
        if excellent_count >= 30:
            optimal_size = min(max_size, excellent_count + good_count)
            reason = f"Rich opportunities ({excellent_count} excellent stocks)"
        elif excellent_count >= 15:
            optimal_size = min_size + int((max_size - min_size) * 0.7)
            reason = f"Good opportunities ({excellent_count} excellent + {good_count} good)"
        elif good_count >= 20:
            optimal_size = min_size + int((max_size - min_size) * 0.5)
            reason = f"Adequate opportunities ({good_count} good stocks)"
        else:
            optimal_size = max(min_size, acceptable_count)
            reason = f"Limited opportunities ({acceptable_count} acceptable)"
        
        logger.info(f"🎯 Portfolio sizing: {optimal_size} stocks - {reason}")
        return optimal_size
    
    def _apply_sector_attractiveness(self, stocks: List[Dict]) -> List[Dict]:
        """Apply sector attractiveness multipliers based on current market"""
        
        # Determine market from first stock (assume all from same market)
        market = 'US' if stocks and not stocks[0]['ticker'].endswith(('.NS', '.BO')) else 'INDIA'
        
        if market == 'US':
            # US sector attractiveness (November 2024)
            sector_multipliers = {
                'Technology': 0.95,              # Overvalued, rate sensitivity
                'Healthcare': 1.05,              # Defensive, aging demographics
                'Industrials': 1.10,             # Reshoring, infrastructure
                'Energy': 1.15,                  # Undervalued, geopolitical premium
                'Financial Services': 1.00,     # Neutral, no concentration issue
                'Consumer Cyclical': 0.95,      # Economic uncertainty
                'Consumer Defensive': 1.05,     # Defensive characteristics
                'Basic Materials': 1.10,        # Commodity cycle, China reopening
                'Utilities': 1.05,              # Rate beneficiary
                'Real Estate': 0.90,            # High rate sensitivity
                'Communication Services': 0.95, # Mature, regulatory concerns
                'Auto Manufacturers': 0.90,     # EV transition challenges
                'Aerospace & Defense': 1.15,    # Geopolitical tensions
                'Biotechnology': 1.00,          # Mixed pipeline outlook
                'Oil & Gas': 1.20,              # Energy transition value play
                'Electric Utilities': 1.10,     # Grid modernization
                'REITs': 0.85,                  # Rate and office space headwinds
                'Software': 0.90,               # AI hype cooling, valuations
                'Semiconductors': 0.95,         # Cyclical concerns
            }
        else:  # India
            # India sector attractiveness
            sector_multipliers = {
                'Financial Services': 0.95,      # Your concentration concern
                'Technology': 1.05,              # Global IT services demand
                'Healthcare': 1.05,              # Defensive + export pharma
                'Auto Manufacturers': 1.15,      # Strong domestic + export growth
                'Aerospace & Defense': 1.15,     # Defense modernization
                'Energy': 1.10,                  # Energy security focus
                'Basic Materials': 1.10,         # Infrastructure spending
                'Aluminum': 1.10,               # Green transition demand
                'Asset Management': 1.10,        # Growing middle class AUM
                'Industrials': 1.05,            # Make in India, infrastructure
                'Consumer Cyclical': 1.05,      # Rising disposable income
                'Consumer Defensive': 1.00,     # Steady growth
                'Utilities': 1.00,              # Steady but regulated
                'Real Estate': 0.95,            # Interest rate concerns
                'Engineering & Construction': 1.10, # Infrastructure boom
                'Drug Manufacturers - Specialty & Generic': 1.10, # Export opportunity
            }
        
        for stock in stocks:
            sector = stock['sector']
            multiplier = sector_multipliers.get(sector, 1.0)  # Default neutral
            
            stock['sector_attractiveness'] = multiplier
            stock['final_score'] = stock['penalty_adjusted_score'] * multiplier
            
            if multiplier != 1.0:
                change = "premium" if multiplier > 1.0 else "discount"
                logger.debug(f"{stock['ticker']} ({market}): {(multiplier-1)*100:+.0f}% sector {change}")
        
        # Final sort by sector-adjusted score
        stocks.sort(key=lambda x: x['final_score'], reverse=True)
        return stocks
    
    def get_portfolio_analytics(self, portfolio: List[Dict]) -> Dict:
        """Generate comprehensive portfolio analytics"""
        if not portfolio:
            return {}
        
        from collections import defaultdict
        import numpy as np
        
        # Basic metrics
        sector_dist = defaultdict(int)
        sector_scores = defaultdict(list)
        
        for stock in portfolio:
            sector = stock['sector']
            sector_dist[sector] += 1
            sector_scores[sector].append(stock['final_score'])
        
        # Calculate metrics
        scores = [s['final_score'] for s in portfolio]
        avg_score = np.mean(scores)
        
        max_sector_count = max(sector_dist.values()) if sector_dist else 0
        max_sector_pct = max_sector_count / len(portfolio) * 100 if portfolio else 0
        
        analytics = {
            'portfolio_size': len(portfolio),
            'sectors_represented': len(sector_dist),
            'avg_quality_score': avg_score,
            'score_range': f"{min(scores):.1f} - {max(scores):.1f}",
            'max_sector_concentration_pct': max_sector_pct,
            'sector_distribution': dict(sector_dist),
            'concentration_risk': (
                'LOW' if max_sector_pct < 25 else 
                'MEDIUM' if max_sector_pct < 35 else 'HIGH'
            ),
            'diversification_quality': (
                'EXCELLENT' if len(sector_dist) >= 8 and max_sector_pct < 20 else
                'GOOD' if len(sector_dist) >= 6 and max_sector_pct < 30 else
                'ADEQUATE' if len(sector_dist) >= 4 else 'POOR'
            )
        }
        
        return analytics
    
    def _log_portfolio_analytics(self, analytics: Dict):
        """Log comprehensive portfolio analytics"""
        logger.info("\n" + "="*70)
        logger.info("QUALITY-FIRST PORTFOLIO ANALYTICS")
        logger.info("="*70)
        logger.info(f"Portfolio Size: {analytics['portfolio_size']} stocks")
        logger.info(f"Sectors Represented: {analytics['sectors_represented']}")
        logger.info(f"Average Quality Score: {analytics['avg_quality_score']:.1f}")
        logger.info(f"Score Range: {analytics['score_range']}")
        logger.info(f"Max Sector Concentration: {analytics['max_sector_concentration_pct']:.1f}%")
        logger.info(f"Concentration Risk: {analytics['concentration_risk']}")
        logger.info(f"Diversification Quality: {analytics['diversification_quality']}")
        
        logger.info("\nSector Breakdown:")
        for sector, count in sorted(analytics['sector_distribution'].items(), 
                                   key=lambda x: x[1], reverse=True):
            pct = count / analytics['portfolio_size'] * 100
            logger.info(f"  {sector:<30}: {count:2d} stocks ({pct:4.1f}%)")
        
        logger.info("="*70)
    
    def filter_by_action(self, stocks: List[Dict], actions: List[str]) -> List[Dict]:
        """Filter stocks by action type"""
        return [s for s in stocks if s['action'] in actions]
    
    def rank_stocks(self, stocks: List[Dict], by: str = 'composite_score') -> List[Dict]:
        """Rank stocks by specified metric"""
        return sorted(stocks, key=lambda x: x.get(by, 0), reverse=True)