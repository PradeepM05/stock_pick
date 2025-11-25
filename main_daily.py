#!/usr/bin/env python3
"""
Daily Stock Screener - GitHub Actions Entry Point
Runs the screener and sends email reports
FIXED VERSION - Handles multiple CSV patterns and better error handling
"""
import argparse
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import os
from email.mime.base import MIMEBase
from email import encoders

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils import setup_logger, load_env_vars


def debug_environment():
    """Debug environment configuration"""
    env_vars = load_env_vars()
    
    print("=== EMAIL CONFIGURATION DEBUG ===")
    print(f"Sender Email: {'✓' if env_vars.get('sender_email') else '❌'} {env_vars.get('sender_email', 'NOT SET')}")
    print(f"Sender Password: {'✓' if env_vars.get('sender_password') else '❌'} {'***' if env_vars.get('sender_password') else 'NOT SET'}")
    print(f"Recipients: {'✓' if env_vars.get('report_recipients') else '❌'} {env_vars.get('report_recipients', 'NOT SET')}")
    
    if env_vars.get('report_recipients'):
        recipients = env_vars.get('report_recipients', '').split(',')
        recipients = [email.strip() for email in recipients if email.strip()]
        print(f"Parsed Recipients: {recipients}")
    
    print("=== OUTPUT DIRECTORY DEBUG ===")
    output_path = Path('output')
    if output_path.exists():
        all_files = list(output_path.glob('*'))
        print(f"Files in output/: {[f.name for f in all_files]}")
        csv_files = list(output_path.glob('*.csv'))
        print(f"CSV files found: {[f.name for f in csv_files]}")
    else:
        print("❌ Output directory does not exist")
    
    print("=================================")


def send_email_report(subject, body, csv_file=None, logger=None):
    """Send email report with results"""
    try:
        env_vars = load_env_vars()
        sender_email = env_vars.get('sender_email')
        sender_password = env_vars.get('sender_password')
        recipients = env_vars.get('report_recipients', '').split(',')
        
        if logger:
            logger.info(f"Email config - Sender: {sender_email}, Recipients: {recipients}")
        
        if not sender_email or not sender_password:
            msg = "❌ Email credentials not configured in .env"
            if logger:
                logger.error(msg)
            else:
                print(msg)
            return False
        
        # Clean up recipients list
        recipients = [r.strip() for r in recipients if r.strip()]
        if not recipients:
            msg = "❌ No recipients configured in .env"
            if logger:
                logger.error(msg)
            else:
                print(msg)
            return False
        
        # Create email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject
        
        if logger:
            logger.info(f"Creating email - Subject: {subject}, To: {msg['To']}")
        
        # Add body
        msg.attach(MIMEText(body, 'html'))
        
        # Attach CSV if provided
        if csv_file and os.path.exists(csv_file):
            if logger:
                logger.info(f"Attaching CSV: {csv_file}")
            with open(csv_file, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{os.path.basename(csv_file)}"'
            )
            msg.attach(part)
        elif csv_file:
            if logger:
                logger.warning(f"CSV file not found for attachment: {csv_file}")
        
        # Send email
        if logger:
            logger.info("Connecting to smtp.gmail.com:587...")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        success_msg = f"✓ Email sent to {msg['To']}"
        if logger:
            logger.info(success_msg)
        else:
            print(success_msg)
        return True
        
    except Exception as e:
        error_msg = f"❌ Error sending email: {e}"
        if logger:
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
        else:
            print(error_msg)
            import traceback
            traceback.print_exc()
        return False


def get_latest_csv(output_dir='output', market='US'):
    """Get the latest CSV file generated - FIXED to handle multiple naming patterns"""
    try:
        output_path = Path(output_dir)
        
        if not output_path.exists():
            print(f"❌ Output directory {output_dir} does not exist")
            return None
        
        # Try multiple patterns to find CSV files
        patterns = [
            f'stock_picks_{market.lower()}_*.csv',      # Original pattern
            f'daily_gems_{market.lower()}_*.csv',       # Your actual pattern from sample
            f'*{market.lower()}*.csv',                  # Broader match
            f'*gems*{market.lower()}*.csv',             # Pattern from sample email
            '*.csv'                                     # Fallback to any CSV
        ]
        
        csv_files = []
        pattern_used = None
        
        for pattern in patterns:
            found_files = list(output_path.glob(pattern))
            if found_files:
                csv_files.extend(found_files)
                pattern_used = pattern
                print(f"✓ Found {len(found_files)} CSV files with pattern: {pattern}")
                break
                
        if csv_files:
            latest_file = max(csv_files, key=os.path.getctime)
            print(f"✓ Using latest file: {latest_file.name} (pattern: {pattern_used})")
            return latest_file
        else:
            print(f"❌ No CSV files found in {output_path}")
            # List all files for debugging
            all_files = list(output_path.glob('*'))
            print(f"Available files: {[f.name for f in all_files if f.is_file()]}")
            
    except Exception as e:
        print(f"❌ Error finding CSV: {e}")
        import traceback
        traceback.print_exc()
    
    return None


def parse_csv_summary(csv_file):
    """Parse CSV to get summary statistics - FIXED to handle different column names"""
    try:
        import pandas as pd
        df = pd.read_csv(csv_file)
        
        print(f"✓ Loaded CSV with {len(df)} rows and columns: {list(df.columns)}")
        
        # Try different possible column names for Action/Rating
        action_columns = ['Action', 'Rating', 'Recommendation', 'Signal']
        action_col = None
        for col in action_columns:
            if col in df.columns:
                action_col = col
                print(f"✓ Using action column: {action_col}")
                break
        
        if action_col:
            strong_buy = len(df[df[action_col] == 'STRONG_BUY'])
            buy = len(df[df[action_col] == 'BUY'])
            watch = len(df[df[action_col].isin(['WATCH', 'SPECULATIVE'])])
        else:
            print(f"⚠️ No action column found. Available columns: {list(df.columns)}")
            # Try to count based on any indication of rating
            strong_buy = buy = watch = 0
        
        # Try different PE ratio column names
        pe_columns = ['PE_Ratio', 'P/E', 'PE', 'pe_ratio', 'PE_Ratio']
        pe_col = None
        for col in pe_columns:
            if col in df.columns:
                pe_col = col
                break
        
        if pe_col:
            # Handle 'N/A', 'nan', None values and convert to float
            pe_values = df[pe_col].replace(['N/A', 'nan', None], pd.NA)
            # Convert to numeric, coercing errors to NaN
            pe_numeric = pd.to_numeric(pe_values, errors='coerce')
            avg_pe = pe_numeric.mean()
        else:
            avg_pe = None
        
        # Try different ROE column names  
        roe_columns = ['ROE_%', 'ROE', 'Return_on_Equity', 'roe', 'ROE_%']
        roe_col = None
        for col in roe_columns:
            if col in df.columns:
                roe_col = col
                break
        
        if roe_col:
            # Handle 'N/A', 'nan', None values and convert to float
            roe_values = df[roe_col].replace(['N/A', 'nan', None], pd.NA)
            # Convert to numeric, coercing errors to NaN
            roe_numeric = pd.to_numeric(roe_values, errors='coerce')
            avg_roe = roe_numeric.mean()
        else:
            avg_roe = None
        
        print(f"✓ Summary: Total={len(df)}, Strong Buy={strong_buy}, Buy={buy}, Watch={watch}")
        
        return {
            'total': len(df),
            'strong_buy': strong_buy,
            'buy': buy,
            'watch': watch,
            'avg_pe': avg_pe,
            'avg_roe': avg_roe,
            'stocks': df.head(10),  # Top 10 for email
            'action_col': action_col,
            'pe_col': pe_col,
            'roe_col': roe_col
        }
    except Exception as e:
        print(f"❌ Error parsing CSV {csv_file}: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_email_body(market_results):
    """Create HTML email body with results for multiple markets"""
    import pandas as pd
    
    current_date = datetime.now().strftime('%B %d, %Y')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
                background-color: #ffffff;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 600;
            }}
            .header p {{
                margin: 10px 0 0 0;
                font-size: 14px;
                opacity: 0.9;
            }}
            .market-section {{
                padding: 30px 20px;
                border-bottom: 1px solid #eee;
            }}
            .market-section:last-child {{
                border-bottom: none;
            }}
            .market-title {{
                font-size: 20px;
                font-weight: 600;
                margin: 0 0 20px 0;
                display: flex;
                align-items: center;
            }}
            .market-title span {{
                margin-right: 10px;
                font-size: 24px;
            }}
            .no-results {{
                color: #999;
                text-align: center;
                padding: 20px;
                background-color: #f9f9f9;
                border-radius: 5px;
            }}
            .summary-cards {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 15px;
                margin-bottom: 25px;
            }}
            .card {{
                background-color: #f9f9f9;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                border-left: 4px solid #667eea;
            }}
            .card.strong-buy {{
                border-left-color: #00a86b;
            }}
            .card.buy {{
                border-left-color: #ffa500;
            }}
            .card.speculative {{
                border-left-color: #dc3545;
            }}
            .card.total {{
                border-left-color: #667eea;
            }}
            .card-value {{
                font-size: 28px;
                font-weight: 600;
                margin: 0 0 5px 0;
                color: #333;
            }}
            .card-label {{
                font-size: 12px;
                text-transform: uppercase;
                color: #666;
                font-weight: 500;
            }}
            .stocks-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            .stocks-table th {{
                background-color: #f8f9fa;
                color: #333;
                font-weight: 600;
                padding: 12px 8px;
                text-align: left;
                border-bottom: 2px solid #dee2e6;
            }}
            .stocks-table td {{
                padding: 10px 8px;
                border-bottom: 1px solid #dee2e6;
                vertical-align: middle;
            }}
            .stocks-table tr:hover {{
                background-color: #f8f9fa;
            }}
            .rank {{
                text-align: center;
                font-weight: 600;
            }}
            .ticker {{
                font-weight: 600;
                color: #333;
            }}
            .strong-buy-badge {{
                background-color: #00a86b;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }}
            .buy-badge {{
                background-color: #ffa500;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }}
            .watch-badge {{
                background-color: #dc3545;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }}
            .footer {{
                padding: 20px;
                text-align: center;
                color: #999;
                font-size: 12px;
                background-color: #f9f9f9;
            }}
            @media (max-width: 600px) {{
                .summary-cards {{
                    grid-template-columns: repeat(2, 1fr);
                }}
                .stocks-table {{
                    font-size: 12px;
                }}
                .stocks-table th, .stocks-table td {{
                    padding: 8px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Daily Hidden Gems Report</h1>
                <p>{current_date}</p>
            </div>
    """
    
    # Add market sections
    for market, summary in market_results.items():
        if market == 'US':
            market_flag = '🇺🇸 US Market'
        elif market == 'INDIA':
            market_flag = '🇮🇳 India Market'
        else:
            market_flag = market
        
        html += f'<div class="market-section"><h2 class="market-title"><span>{market_flag.split()[0]}</span>{market_flag.split(maxsplit=1)[1]}</h2>'
        
        if not summary:
            html += '<div class="no-results">No results available for this market today.</div>'
        else:
            # Summary cards
            html += '<div class="summary-cards">'
            html += f'<div class="card strong-buy"><div class="card-value">{summary.get("strong_buy", 0)}</div><div class="card-label">Strong Buy</div></div>'
            html += f'<div class="card buy"><div class="card-value">{summary.get("buy", 0)}</div><div class="card-label">Buy</div></div>'
            html += f'<div class="card speculative"><div class="card-value">{summary.get("watch", 0)}</div><div class="card-label">Speculative</div></div>'
            html += f'<div class="card total"><div class="card-value">{summary.get("total", 0)}</div><div class="card-label">Total Analyzed</div></div>'
            html += '</div>'
            
            # Stocks table
            html += """
            <table class="stocks-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Ticker</th>
                        <th>Company</th>
                        <th>Price</th>
                        <th>P/E</th>
                        <th>ROE</th>
                        <th>Score</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            # Get column names from summary
            action_col = summary.get('action_col', 'Action')
            stocks_df = summary['stocks']
            
            for idx, row in stocks_df.iterrows():
                action = row.get(action_col, 'N/A')
                
                if action == 'STRONG_BUY':
                    badge = f'<span class="strong-buy-badge">{action}</span>'
                elif action == 'BUY':
                    badge = f'<span class="buy-badge">{action}</span>'
                else:
                    badge = f'<span class="watch-badge">{action}</span>'
                
                # Try to get ticker from different possible column names
                ticker_cols = ['Ticker', 'Symbol', 'Stock', 'ticker']
                ticker = 'N/A'
                for col in ticker_cols:
                    if col in row and pd.notna(row[col]):
                        ticker = row[col]
                        break
                
                # Try to get company name
                company_cols = ['Company', 'Name', 'company_name', 'Company_Name']
                company = 'N/A'
                for col in company_cols:
                    if col in row and pd.notna(row[col]):
                        company = str(row[col])[:30]
                        if len(str(row[col])) > 30:
                            company += '...'
                        break
                
                # Try to get price
                price_cols = ['Market_Price', 'Price', 'Current_Price', 'current_price', 'Close']
                price = 'N/A'
                for col in price_cols:
                    if col in row and pd.notna(row[col]):
                        try:
                            price_val = float(row[col])
                            price = f"{price_val:.2f}"
                            break
                        except:
                            continue
                
                # Get PE and ROE
                pe_col = summary.get('pe_col', 'PE_Ratio')
                roe_col = summary.get('roe_col', 'ROE_%')
                
                pe = row.get(pe_col, 'N/A')
                roe = row.get(roe_col, 'N/A')
                
                # Try to get score
                score_cols = ['Composite_Score', 'Score', 'Rating_Score', 'composite_score']
                score = 'N/A'
                for col in score_cols:
                    if col in row and pd.notna(row[col]):
                        try:
                            score_val = float(row[col])
                            score = f"{score_val:.1f}"
                            break
                        except:
                            continue
                
                html += f"""
                    <tr>
                        <td class="rank">{idx + 1}</td>
                        <td class="ticker">{ticker}</td>
                        <td>{company}</td>
                        <td>{price}</td>
                        <td>{pe}</td>
                        <td>{roe}</td>
                        <td><strong>{score}</strong></td>
                        <td>{badge}</td>
                    </tr>
                """
            
            html += """
                </tbody>
            </table>
            """
        
        html += '</div>'
    
    html += f"""
        <div class="footer">
            <p>This is an automated report from your Daily Hidden Gems Stock Screener.<br>
            Full CSV results are available in the repository. For more information, visit the GitHub repository.</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>⚠️ This is not investment advice. Always do your own research before investing.</p>
        </div>
        </div>
    </body>
    </html>
    """
    
    return html


def main():
    """Main function for GitHub Actions"""
    parser = argparse.ArgumentParser(description='Daily Stock Screener with Email Report')
    parser.add_argument(
        '--market',
        type=str,
        choices=['US', 'INDIA', 'BOTH'],
        default='US',
        help='Market to screen'
    )
    parser.add_argument(
        '--send-email',
        action='store_true',
        help='Send email report after screening'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable cache and fetch fresh data'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Debug mode - show environment and file info'
    )
    
    args = parser.parse_args()
    
    logger = setup_logger(__name__)
    logger.info(f"🚀 Starting daily screening: {args.market} market")
    
    if args.debug:
        debug_environment()
    
    try:
        # Determine markets to screen
        markets_to_screen = ['US', 'INDIA'] if args.market == 'BOTH' else [args.market]
        market_results = {}
        
        for market in markets_to_screen:
            # Build main.py command
            cmd = ['python', 'main.py', '--market', market]
            if args.no_cache:
                cmd.append('--no-cache')
            
            # Run main screener
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=False, text=True)
            
            if result.returncode != 0:
                logger.error(f"❌ Screening for {market} failed with exit code {result.returncode}")
                market_results[market] = None
                continue
            
            logger.info(f"✓ Screening for {market} completed successfully")
            
            # Get latest CSV with improved detection
            csv_file = get_latest_csv('output', market)
            if csv_file:
                logger.info(f"Found results: {csv_file}")
                summary = parse_csv_summary(csv_file)
                if summary:
                    market_results[market] = summary
                    market_results[market]['csv_file'] = csv_file  # Store for attachment
                else:
                    logger.warning(f"Could not parse CSV for {market}")
                    market_results[market] = None
            else:
                logger.warning(f"No CSV file found for {market}")
                market_results[market] = None
        
        logger.info("✓ All screening completed")
        
        # Send email if requested
        if args.send_email:
            logger.info("📧 Preparing email report...")
            try:
                email_body = create_email_body(market_results)
                logger.info("✓ Email body generated successfully")
                
                # Find CSV file to attach (prefer INDIA if available, then US)
                csv_file = None
                for market in ['INDIA', 'US']:
                    if market in market_results and market_results[market] and 'csv_file' in market_results[market]:
                        csv_file = market_results[market]['csv_file']
                        logger.info(f"Using CSV from {market} market: {csv_file}")
                        break
                
                if not csv_file:
                    # Try generic approach
                    csv_file = get_latest_csv('output', 'INDIA') or get_latest_csv('output', 'US')
                
                logger.info(f"CSV file to attach: {csv_file}")
                
                subject = f"📊 Daily Hidden Gems Report - {datetime.now().strftime('%B %d, %Y')}"
                logger.info(f"Sending email with subject: {subject}")
                
                if args.debug:
                    logger.info("DEBUG mode: Email prepared but not sent")
                    print("Email body preview:")
                    print(email_body[:500] + "...")
                else:
                    send_email_report(subject, email_body, csv_file, logger=logger)
                    
            except Exception as e:
                logger.error(f"❌ Error preparing email: {e}")
                import traceback
                logger.error(traceback.format_exc())
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()