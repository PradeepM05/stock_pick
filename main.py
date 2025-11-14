"""
Stock Screener - Main Entry Point with Full Analysis
"""
import argparse
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.screeners import create_screener
from src.data import CacheManager, BulkFetcher
from src.config import get_market_config, CACHE_DIR, OUTPUT_DIR, ACTION_THRESHOLDS, SECTOR_BENCHMARKS
from src.analysis import StockScorer
from src.utils import setup_logger, load_env_vars
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm  # For progress bar


def main():
    """Main function with full analysis pipeline"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Stock Screener with Full Analysis')
    parser.add_argument(
        '--market',
        type=str,
        choices=['US', 'INDIA', 'BOTH'],
        default='US',
        help='Market to screen (default: US)'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable cache and fetch fresh data'
    )
    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear cache before running'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--top-n',
        type=int,
        default=20,
        help='Number of top stocks to return (default: 20)'
    )
    parser.add_argument(
        '--analyze-all',
        action='store_true',
        help='Analyze all stocks (default: analyze top-n only)'
    )
    
    args = parser.parse_args()
    
    # Setup logger
    logger = setup_logger(level=args.log_level)
    logger.info("=" * 70)
    logger.info("STOCK SCREENER v2.0 - WITH FULL ANALYSIS")
    logger.info("=" * 70)
    
    # Load environment variables
    env_vars = load_env_vars()
    api_key = env_vars.get('yahoo_api_key')
    
    if not api_key:
        logger.warning("WARNING: No Yahoo Finance API key found")
        logger.warning("   Set YAHOO_FINANCE_API_KEY in .env file for full functionality")
        logger.info("   Continuing with FREE data sources...")
    
    # Initialize cache manager
    cache_manager = CacheManager(CACHE_DIR)
    
    # Clear cache if requested
    if args.clear_cache:
        logger.info("Clearing cache...")
        cache_manager.clear(market=args.market if args.market != 'BOTH' else None)
    
    # Get market configuration
    market_config = get_market_config(args.market)
    
    # STEP 1: Screen stocks (get ticker list)
    logger.info(f"\n{'=' * 70}")
    logger.info(f"STEP 1: FETCHING {args.market} STOCK LIST")
    logger.info('=' * 70)
    
    screener = create_screener(
        market=args.market,
        filters=market_config['filters'],
        cache_manager=cache_manager,
        api_key=api_key
    )
    
    all_tickers = screener.screen_stocks(use_cache=not args.no_cache)
    
    if not all_tickers:
        logger.error("No stocks found in initial screening. Exiting.")
        return
    
    logger.info(f"\n✓ Found {len(all_tickers)} tickers to screen")
    
    # STEP 2: BULK FETCH & PRE-FILTER (NEW!)
    logger.info(f"\n{'=' * 70}")
    logger.info(f"STEP 2: BULK FETCHING FUNDAMENTALS & PRE-FILTERING")
    logger.info(f"This efficient approach saves 90% of API calls!")
    logger.info('=' * 70)
    
    bulk_fetcher = BulkFetcher(max_workers=10)
    
    # Fetch basic fundamentals for all stocks
    stocks_data = bulk_fetcher.fetch_basic_fundamentals(all_tickers, batch_size=50)
    
    if not stocks_data:
        logger.error("Failed to fetch fundamental data. Exiting.")
        return
    
    logger.info(f"\n✓ Fetched fundamentals for {len(stocks_data)} stocks")
    
    # Apply filters to get candidates
    filtered_tickers = bulk_fetcher.apply_filters(stocks_data, market_config['filters'])
    
    if not filtered_tickers:
        logger.warning("No stocks passed filters. Try adjusting filter criteria in config.")
        logger.info("\nShowing top 10 stocks by market cap (no filtering):")
        sorted_stocks = sorted(stocks_data.items(), 
                             key=lambda x: x[1].get('market_cap', 0), 
                             reverse=True)[:10]
        for i, (ticker, data) in enumerate(sorted_stocks, 1):
            logger.info(f"  {i}. {ticker} - {data.get('name')} | "
                       f"MCap: ${data.get('market_cap', 0)/1e9:.1f}B | "
                       f"P/E: {data.get('pe_ratio', 'N/A')}")
        return
    
    logger.info(f"\n✓ {len(filtered_tickers)} stocks passed all filters")
    logger.info(f"   Reduction: {len(all_tickers)} → {len(filtered_tickers)} stocks")
    logger.info(f"   API calls saved: ~{(len(all_tickers) - len(filtered_tickers)) * 2}")
    
    # Limit to top-n for analysis if specified
    tickers_to_analyze = filtered_tickers[:args.top_n * 2] if not args.analyze_all else filtered_tickers
    
    # STEP 3: DEEP ANALYSIS (only on filtered stocks!)
    logger.info(f"\n{'=' * 70}")
    logger.info(f"STEP 3: DEEP ANALYSIS ON {len(tickers_to_analyze)} FILTERED STOCKS")
    logger.info(f"Estimated time: {len(tickers_to_analyze) * 2 // 60} minutes")
    logger.info('=' * 70)
    
    # Initialize scorer WITH SECTOR BENCHMARKS
    scorer = StockScorer(
        valuation_thresholds=market_config.get('valuation_thresholds', {}),
        action_thresholds=ACTION_THRESHOLDS,
        sector_benchmarks=SECTOR_BENCHMARKS  # NEW!
    )
    
    # Analyze stocks WITH PARALLEL PROCESSING
    analyzed_stocks = []
    failed_count = 0
    
    logger.info("→ Using parallel processing (5 workers) for faster analysis...")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all analysis tasks
        future_to_ticker = {
            executor.submit(scorer.score_stock, ticker): ticker
            for ticker in tickers_to_analyze
        }
        
        # Process results with progress bar
        with tqdm(total=len(tickers_to_analyze), desc="Analyzing stocks", unit="stock") as pbar:
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    result = future.result()
                    if result:
                        analyzed_stocks.append(result)
                        logger.info(f"   ✓ {ticker}: {result['action']} (Score={result['composite_score']:.1f})")
                    else:
                        failed_count += 1
                        logger.warning(f"   ✗ {ticker}: Failed")
                except Exception as e:
                    failed_count += 1
                    logger.error(f"   ✗ {ticker}: Error - {e}")
                finally:
                    pbar.update(1)
    
    logger.info(f"\n{'=' * 70}")
    logger.info(f"Analysis Complete: {len(analyzed_stocks)} stocks analyzed successfully")
    logger.info(f"Failed: {failed_count} stocks")
    logger.info('=' * 70)
    
    if not analyzed_stocks:
        logger.error("No stocks successfully analyzed. Exiting.")
        return
    
    # STEP 4: Filter and rank
    logger.info(f"\n{'=' * 70}")
    logger.info("STEP 4: FILTERING AND RANKING")
    logger.info('=' * 70)
    
    # Get stocks by action category
    strong_buy_stocks = scorer.filter_by_action(analyzed_stocks, actions=['STRONG_BUY'])
    buy_stocks = scorer.filter_by_action(analyzed_stocks, actions=['BUY'])
    speculative_stocks = scorer.filter_by_action(analyzed_stocks, actions=['SPECULATIVE'])
    
    logger.info(f"STRONG_BUY: {len(strong_buy_stocks)} stocks")
    logger.info(f"BUY: {len(buy_stocks)} stocks")  
    logger.info(f"SPECULATIVE: {len(speculative_stocks)} stocks")
    
    # Combine for display (prioritize STRONG_BUY, then BUY, then SPECULATIVE)
    all_recommendation_stocks = strong_buy_stocks + buy_stocks + speculative_stocks
    
    # If we have too few recommendations, try finding simple gems from filtered stocks
    if len(all_recommendation_stocks) < 10:
        logger.info(f"\n💎 Only {len(all_recommendation_stocks)} stocks passed full analysis")
        logger.info("🔍 Looking for additional hidden gems from filtered stocks...")
        
        # Get stocks data for filtered tickers
        filtered_stocks_data = {}
        for ticker in filtered_tickers[:50]:  # Check top 50 filtered stocks
            if ticker not in [s['ticker'] for s in analyzed_stocks]:  # Not already analyzed
                try:
                    stock_data = bulk_fetcher._fetch_single(ticker)
                    if stock_data:
                        filtered_stocks_data[ticker] = stock_data
                except:
                    continue
        
        # Find simple gems
        gem_tickers = bulk_fetcher.find_simple_gems(filtered_stocks_data, max_results=10)
        
        logger.info(f"🏆 Found {len(gem_tickers)} additional hidden gems")
        for i, ticker in enumerate(gem_tickers[:5], 1):
            data = filtered_stocks_data[ticker]
            score = bulk_fetcher._simple_gem_score(data)
            logger.info(f"  {i}. {ticker} - Gem Score: {score:.1f} | "
                       f"P/E: {data.get('pe_ratio', 'N/A')} | "
                       f"ROE: {data.get('roe', 'N/A')}% | "
                       f"MCap: ${data.get('market_cap', 0)/1e6:.0f}M")
    
    # Rank by composite score within each category
    top_stocks = scorer.rank_stocks(all_recommendation_stocks, by='composite_score')[:args.top_n]
    logger.info(f"Top {len(top_stocks)} recommendations selected")
    
    # STEP 5: Display results
    logger.info(f"\n{'=' * 70}")
    logger.info("STEP 5: TOP STOCK RECOMMENDATIONS")
    logger.info('=' * 70)
    
    if not top_stocks:
        logger.warning("No stocks meet the recommendation criteria")
        # Show top 10 from all analyzed stocks
        logger.info("\nShowing top 10 stocks by score (all actions):")
        all_ranked = scorer.rank_stocks(analyzed_stocks, by='composite_score')
        for i, stock in enumerate(all_ranked[:10], 1):
            print_stock_summary(logger, stock, i)
    else:
        for i, stock in enumerate(top_stocks, 1):
            print_stock_summary(logger, stock, i)
    
    # STEP 6: Save to CSV
    logger.info(f"\n{'=' * 70}")
    logger.info("STEP 6: SAVING RESULTS")
    logger.info('=' * 70)
    
    if top_stocks:
        save_results_to_csv(top_stocks, args.market, logger)
    else:
        logger.warning("No results to save")
    
    logger.info(f"\n{'=' * 70}")
    logger.info("📈 HIDDEN GEMS SUMMARY")
    logger.info('=' * 70)
    logger.info(f"\nTotal Analyzed: {len(analyzed_stocks)} stocks")
    logger.info(f"STRONG_BUY: {len(strong_buy_stocks)} stocks")  
    logger.info(f"BUY: {len(buy_stocks)} stocks")
    logger.info(f"SPECULATIVE: {len(speculative_stocks)} stocks")
    logger.info(f"Top Picks: {len(top_stocks)} stocks")
    logger.info(f"\n💎 FOCUS: Quality over quantity - these are your best opportunities!")
    logger.info(f"📁 Results saved to: {OUTPUT_DIR}/")
    
    # Show key metrics of top picks
    if top_stocks:
        logger.info(f"\n🏆 TOP PICKS SUMMARY:")
        avg_pe = sum(s.get('pe_ratio', 0) for s in top_stocks if s.get('pe_ratio')) / len(top_stocks)
        avg_roe = sum(s.get('roe', 0) for s in top_stocks if s.get('roe')) / len(top_stocks)
        avg_mcap = sum(s.get('market_cap', 0) for s in top_stocks) / len(top_stocks) / 1e6
        
        logger.info(f"   Average P/E: {avg_pe:.1f}")
        logger.info(f"   Average ROE: {avg_roe:.1f}%") 
        logger.info(f"   Average Market Cap: ${avg_mcap:.0f}M")
        logger.info(f"   Sectors: {', '.join(set(s.get('sector', 'Unknown') for s in top_stocks))}")



def print_stock_summary(logger, stock, rank):
    """Print formatted stock summary"""
    logger.info(f"\n{rank}. {stock['ticker']} - {stock['company_name']}")
    logger.info(f"   Sector: {stock['sector']}")
    logger.info(f"   Action: {stock['action']} | Composite Score: {stock['composite_score']:.1f}")
    logger.info(f"   Valuation: {stock['valuation_score']:.1f} | Technical: {stock['technical_score']:.1f}")
    logger.info(f"   Price: ${stock['current_price']:.2f} | P/E: {stock.get('pe_ratio', 'N/A')}")
    logger.info(f"   ROE: {stock.get('roe', 'N/A')}% | Debt/Equity: {stock.get('debt_to_equity', 'N/A')}")
    logger.info(f"   → {stock['description']}")


def save_results_to_csv(stocks, market, logger):
    """Save analysis results to CSV"""
    # Prepare data
    rows = []
    for stock in stocks:
        row = {
            'Rank': len(rows) + 1,
            'Ticker': stock['ticker'],
            'Company': stock['company_name'],
            'Sector': stock['sector'],
            'Industry': stock['industry'],
            'Action': stock['action'],
            'Composite_Score': round(stock['composite_score'], 2),
            'Valuation_Score': round(stock['valuation_score'], 2),
            'Technical_Score': round(stock['technical_score'], 2),
            'Current_Price': round(stock.get('current_price', 0), 2),
            'Market_Cap': stock.get('market_cap', 0),
            'PE_Ratio': round(stock.get('pe_ratio', 0), 2) if stock.get('pe_ratio') else 'N/A',
            'ROE_%': round(stock.get('roe', 0), 2) if stock.get('roe') else 'N/A',
            'Debt_to_Equity': round(stock.get('debt_to_equity', 0), 2) if stock.get('debt_to_equity') else 'N/A',
            'Earnings_Growth_%': round(stock.get('earnings_growth', 0), 2) if stock.get('earnings_growth') else 'N/A',
            'Trend': stock.get('trend', 'Unknown'),
            'RSI': round(stock.get('rsi', 0), 2) if stock.get('rsi') else 'N/A',
            'Description': stock['description']
        }
        rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"stock_picks_{market.lower()}_{timestamp}.csv"
    filepath = Path(OUTPUT_DIR) / filename
    
    # Ensure output directory exists
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(filepath, index=False)
    logger.info(f"\n✓ Results saved to: {filepath}")
    logger.info(f"   Columns: {', '.join(df.columns)}")
    logger.info(f"   Rows: {len(df)}")



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScreening interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)