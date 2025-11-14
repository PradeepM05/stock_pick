"""
Enhanced Stock Screener - Daily Automated Version with Email Reports
Runs both US and India markets and sends comprehensive email reports
"""
import argparse
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import json
import traceback

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.screeners import create_screener
from src.data import CacheManager, BulkFetcher
from src.config import get_market_config, CACHE_DIR, OUTPUT_DIR, ACTION_THRESHOLDS, SECTOR_BENCHMARKS
from src.analysis import StockScorer
from src.utils import setup_logger, load_env_vars
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Import email reporter (will be in same directory)
try:
    from email_reporter import EmailReporter
except ImportError:
    EmailReporter = None

def main():
    """Enhanced main function for automated daily runs"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Hidden Gems Stock Screener - Daily Automated Version')
    parser.add_argument(
        '--market',
        type=str,
        choices=['US', 'INDIA', 'BOTH'],
        default='BOTH',
        help='Market to screen (default: BOTH for daily runs)'
    )
    parser.add_argument(
        '--send-email',
        action='store_true',
        help='Send email report after completion'
    )
    parser.add_argument(
        '--email-recipients',
        type=str,
        nargs='+',
        help='Email recipients (overrides env variable)'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable cache and fetch fresh data'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Custom output directory'
    )
    
    args = parser.parse_args()
    
    # Setup logger
    logger = setup_logger(level=args.log_level)
    
    # Store results for email reporting
    results = {
        'us': None,
        'india': None,
        'files': [],
        'errors': []
    }
    
    try:
        logger.info("=" * 70)
        logger.info("📈 DAILY HIDDEN GEMS SCREENER")
        logger.info(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)
        
        # Load environment variables
        env_vars = load_env_vars()
        api_key = env_vars.get('yahoo_api_key')
        
        if not api_key:
            logger.warning("⚠️ No Yahoo Finance API key found - using fallback data sources")
        
        # Initialize cache manager
        cache_manager = CacheManager(CACHE_DIR)
        
        # Force fresh data for daily runs
        if args.no_cache:
            logger.info("🧹 Clearing cache for fresh daily data...")
            cache_manager.clear()
        
        # Run markets based on selection
        markets_to_run = ['US', 'INDIA'] if args.market == 'BOTH' else [args.market]
        
        for market in markets_to_run:
            try:
                logger.info(f"\n{'=' * 70}")
                logger.info(f"🌍 PROCESSING {market} MARKET")
                logger.info('=' * 70)
                
                market_results = run_market_screening(market, cache_manager, api_key, logger)
                
                if market_results:
                    results[market.lower()] = market_results['stocks']
                    results['files'].extend(market_results['files'])
                    logger.info(f"✅ {market} market completed successfully")
                else:
                    logger.warning(f"⚠️ {market} market returned no results")
                    
            except Exception as e:
                error_msg = f"❌ Error processing {market} market: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        # Generate summary
        generate_daily_summary(results, logger)
        
        # Send email report if requested
        if args.send_email:
            send_email_report(results, args.email_recipients, logger)
        
        logger.info(f"\n{'=' * 70}")
        logger.info("🎉 DAILY SCREENING COMPLETED")
        logger.info(f"🕐 Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info('=' * 70)
        
    except Exception as e:
        error_msg = f"💥 Critical error in daily screening: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        results['errors'].append(error_msg)
        
        # Send error notification email
        if args.send_email and EmailReporter:
            try:
                email_reporter = EmailReporter()
                email_reporter.send_error_notification(
                    error_msg + "\n\n" + traceback.format_exc(),
                    args.email_recipients
                )
            except:
                pass


def run_market_screening(market: str, cache_manager, api_key: str, logger) -> dict:
    """Run screening for a specific market"""
    
    try:
        # Get market configuration
        market_config = get_market_config(market)
        
        # STEP 1: Screen stocks (get ticker list)
        logger.info(f"📊 STEP 1: Fetching {market} stock universe...")
        
        screener = create_screener(
            market=market,
            filters=market_config['filters'],
            cache_manager=cache_manager,
            api_key=api_key
        )
        
        all_tickers = screener.screen_stocks(use_cache=False)  # Fresh data for daily runs
        
        if not all_tickers:
            logger.error(f"No stocks found for {market} market")
            return None
        
        logger.info(f"✅ Found {len(all_tickers)} {market} stocks to analyze")
        
        # STEP 2: Bulk fetch fundamentals
        logger.info(f"📈 STEP 2: Fetching fundamentals for {market} stocks...")
        
        bulk_fetcher = BulkFetcher(max_workers=10)
        stocks_data = bulk_fetcher.fetch_basic_fundamentals(all_tickers, batch_size=50)
        
        if not stocks_data:
            logger.error(f"Failed to fetch fundamental data for {market}")
            return None
        
        logger.info(f"✅ Retrieved data for {len(stocks_data)} {market} stocks")
        
        # STEP 3: Apply filters
        logger.info(f"🔍 STEP 3: Applying {market} filters...")
        
        filtered_tickers = bulk_fetcher.apply_filters(stocks_data, market_config['filters'])
        
        if not filtered_tickers:
            logger.warning(f"No {market} stocks passed filters")
            return None
        
        logger.info(f"✅ {len(filtered_tickers)} {market} stocks passed filters")
        
        # Limit analysis for daily runs (top 50 per market)
        tickers_to_analyze = filtered_tickers[:50]
        
        # STEP 4: Detailed analysis
        logger.info(f"🔬 STEP 4: Analyzing top {len(tickers_to_analyze)} {market} stocks...")
        
        scorer = StockScorer(
            valuation_thresholds=market_config.get('valuation_thresholds', {}),
            action_thresholds=ACTION_THRESHOLDS,
            sector_benchmarks=SECTOR_BENCHMARKS
        )
        
        analyzed_stocks = []
        
        # Analyze with progress tracking
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_ticker = {
                executor.submit(scorer.score_stock, ticker): ticker
                for ticker in tickers_to_analyze
            }
            
            with tqdm(total=len(tickers_to_analyze), desc=f"Analyzing {market}", unit="stock") as pbar:
                for future in as_completed(future_to_ticker):
                    ticker = future_to_ticker[future]
                    try:
                        result = future.result()
                        if result:
                            analyzed_stocks.append(result)
                    except Exception as e:
                        logger.debug(f"Failed to analyze {ticker}: {e}")
                    finally:
                        pbar.update(1)
        
        logger.info(f"✅ Analyzed {len(analyzed_stocks)} {market} stocks successfully")
        
        # STEP 5: Filter and rank results
        if not analyzed_stocks:
            logger.warning(f"No {market} stocks completed analysis")
            return None
        
        # Get stocks by action
        strong_buy_stocks = scorer.filter_by_action(analyzed_stocks, actions=['STRONG_BUY'])
        buy_stocks = scorer.filter_by_action(analyzed_stocks, actions=['BUY'])
        speculative_stocks = scorer.filter_by_action(analyzed_stocks, actions=['SPECULATIVE'])
        
        # Combine for final results (top 20 per market)
        all_recommendation_stocks = strong_buy_stocks + buy_stocks + speculative_stocks
        final_stocks = scorer.rank_stocks(all_recommendation_stocks, by='composite_score')[:20]
        
        # STEP 6: Save results
        output_file = save_market_results(final_stocks, market, logger)
        
        logger.info(f"🎯 {market} RESULTS:")
        logger.info(f"   STRONG_BUY: {len(strong_buy_stocks)} stocks")
        logger.info(f"   BUY: {len(buy_stocks)} stocks")
        logger.info(f"   SPECULATIVE: {len(speculative_stocks)} stocks")
        logger.info(f"   📁 Saved to: {output_file}")
        
        return {
            'stocks': final_stocks,
            'files': [output_file],
            'summary': {
                'total_analyzed': len(analyzed_stocks),
                'strong_buy': len(strong_buy_stocks),
                'buy': len(buy_stocks),
                'speculative': len(speculative_stocks)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in {market} market screening: {e}")
        raise


def save_market_results(stocks: list, market: str, logger) -> str:
    """Save market results to CSV"""
    if not stocks:
        return None
    
    # Prepare data for CSV
    rows = []
    for rank, stock in enumerate(stocks, 1):
        row = {
            'Rank': rank,
            'Ticker': stock['ticker'],
            'Company': stock['company_name'],
            'Sector': stock['sector'],
            'Industry': stock['industry'],
            'Action': stock['action'],
            'Composite_Score': round(stock['composite_score'], 2),
            'Valuation_Score': round(stock['valuation_score'], 2),
            'Technical_Score': round(stock['technical_score'], 2),
            'Current_Price': round(stock.get('current_price', 0), 2),
            'Market_Cap_M': round(stock.get('market_cap', 0) / 1e6, 1),
            'PE_Ratio': round(stock.get('pe_ratio', 0), 2) if stock.get('pe_ratio') else 'N/A',
            'ROE_%': round(stock.get('roe', 0), 2) if stock.get('roe') else 'N/A',
            'Debt_to_Equity': round(stock.get('debt_to_equity', 0), 2) if stock.get('debt_to_equity') is not None else 'N/A',
            'Revenue_Growth_%': round(stock.get('revenue_growth', 0), 2) if stock.get('revenue_growth') else 'N/A',
            'Description': stock.get('description', '')
        }
        rows.append(row)
    
    # Create DataFrame and save
    df = pd.DataFrame(rows)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"daily_gems_{market.lower()}_{timestamp}.csv"
    filepath = Path(OUTPUT_DIR) / filename
    
    # Ensure output directory exists
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    df.to_csv(filepath, index=False)
    return str(filepath)


def generate_daily_summary(results: dict, logger):
    """Generate and log daily summary"""
    logger.info(f"\n{'=' * 70}")
    logger.info("📊 DAILY SUMMARY")
    logger.info('=' * 70)
    
    total_us = len(results['us']) if results['us'] else 0
    total_india = len(results['india']) if results['india'] else 0
    
    logger.info(f"🇺🇸 US Market: {total_us} hidden gems found")
    logger.info(f"🇮🇳 India Market: {total_india} hidden gems found")
    logger.info(f"📁 Output files: {len(results['files'])}")
    
    if results['errors']:
        logger.warning(f"⚠️ Errors encountered: {len(results['errors'])}")
        for error in results['errors']:
            logger.warning(f"   - {error}")


def send_email_report(results: dict, recipients: list, logger):
    """Send email report with results"""
    if not EmailReporter:
        logger.error("Email reporter not available - cannot send email")
        return
    
    try:
        logger.info("📧 Sending email report...")
        
        email_reporter = EmailReporter()
        
        success = email_reporter.send_daily_report(
            us_results=results['us'],
            india_results=results['india'],
            recipients=recipients,
            attachment_files=results['files']
        )
        
        if success:
            logger.info("✅ Email report sent successfully")
        else:
            logger.error("❌ Failed to send email report")
            
    except Exception as e:
        logger.error(f"❌ Error sending email: {e}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Daily screening interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n💥 Critical error: {e}")
        sys.exit(1)