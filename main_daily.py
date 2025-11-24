#!/usr/bin/env python3
"""
Daily Stock Screener - GitHub Actions Entry Point
Runs the screener and sends email reports
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

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils import setup_logger, load_env_vars


def send_email_report(subject, body, csv_file=None):
    """Send email report with results"""
    try:
        env_vars = load_env_vars()
        sender_email = env_vars.get('sender_email')
        sender_password = env_vars.get('sender_password')
        recipients = env_vars.get('report_recipients', '').split(',')
        
        if not sender_email or not sender_password or not recipients:
            print("❌ Email credentials not configured in .env")
            return False
        
        # Create email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join([r.strip() for r in recipients if r.strip()])
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'html'))
        
        # Attach CSV if provided
        if csv_file and os.path.exists(csv_file):
            with open(csv_file, 'rb') as attachment:
                msg.add_attachment(
                    attachment.read(),
                    maintype='text',
                    subtype='csv',
                    filename=os.path.basename(csv_file)
                )
        
        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print(f"✓ Email sent to {msg['To']}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


def get_latest_csv(output_dir='output', market='US'):
    """Get the latest CSV file generated"""
    try:
        output_path = Path(output_dir)
        csv_files = list(output_path.glob(f'stock_picks_{market.lower()}_*.csv'))
        if csv_files:
            # Return the most recent file
            return max(csv_files, key=os.path.getctime)
    except Exception as e:
        print(f"⚠ Could not find CSV: {e}")
    
    return None


def parse_csv_summary(csv_file):
    """Parse CSV to get summary statistics"""
    try:
        import pandas as pd
        df = pd.read_csv(csv_file)
        
        strong_buy = len(df[df['Action'] == 'STRONG_BUY'])
        buy = len(df[df['Action'] == 'BUY'])
        watch = len(df[df['Action'] == 'WATCH'])
        
        avg_pe = df['PE_Ratio'].replace('N/A', None).astype(float, errors='ignore').mean()
        avg_roe = df['ROE_%'].replace('N/A', None).astype(float, errors='ignore').mean()
        
        return {
            'total': len(df),
            'strong_buy': strong_buy,
            'buy': buy,
            'watch': watch,
            'avg_pe': avg_pe,
            'avg_roe': avg_roe,
            'stocks': df.head(10)  # Top 10 for email
        }
    except Exception as e:
        print(f"⚠ Error parsing CSV: {e}")
        return None


def create_email_body(market_results):
    """Create HTML email body with results for multiple markets"""
    
    current_date = datetime.now().strftime('%B %d, %Y')
    
    html = """
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
                font-weight: 700;
                margin: 10px 0;
            }}
            .card-label {{
                font-size: 12px;
                color: #666;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .stocks-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }}
            .stocks-table thead {{
                background-color: #f9f9f9;
            }}
            .stocks-table th {{
                padding: 12px;
                text-align: left;
                font-weight: 600;
                font-size: 12px;
                color: #333;
                border-bottom: 2px solid #ddd;
            }}
            .stocks-table td {{
                padding: 12px;
                border-bottom: 1px solid #eee;
                font-size: 13px;
            }}
            .stocks-table tr:hover {{
                background-color: #f9f9f9;
            }}
            .rank {{
                font-weight: 600;
                color: #667eea;
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
                <p>{}</p>
            </div>
    """.format(current_date)
    
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
            
            for idx, row in summary['stocks'].iterrows():
                if row['Action'] == 'STRONG_BUY':
                    badge = f'<span class="strong-buy-badge">{row["Action"]}</span>'
                elif row['Action'] == 'BUY':
                    badge = f'<span class="buy-badge">{row["Action"]}</span>'
                else:
                    badge = f'<span class="watch-badge">{row["Action"]}</span>'
                
                html += f"""
                    <tr>
                        <td class="rank">{idx + 1}</td>
                        <td class="ticker">{row['Ticker']}</td>
                        <td>{row['Company']}</td>
                        <td>{row.get('Market_Price', 'N/A')}</td>
                        <td>{row['PE_Ratio']}</td>
                        <td>{row['ROE_%']}</td>
                        <td><strong>{row['Composite_Score']:.1f}</strong></td>
                        <td>{badge}</td>
                    </tr>
                """
            
            html += """
                </tbody>
            </table>
            """
        
        html += '</div>'
    
    html += """
        <div class="footer">
            <p>This is an automated report from your Daily Hidden Gems Stock Screener.<br>
            Full CSV results are available in the repository. For more information, visit the GitHub repository.</p>
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
    
    args = parser.parse_args()
    
    logger = setup_logger(__name__)
    logger.info(f"🚀 Starting daily screening: {args.market} market")
    
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
            
            # Get latest CSV
            csv_file = get_latest_csv('output', market)
            if csv_file:
                logger.info(f"Found results: {csv_file}")
                summary = parse_csv_summary(csv_file)
                if summary:
                    market_results[market] = summary
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
            email_body = create_email_body(market_results)
            
            # Find CSV file to attach (prefer US if available, otherwise INDIA)
            csv_file = get_latest_csv('output', 'US') or get_latest_csv('output', 'INDIA')
            
            subject = f"📊 Daily Hidden Gems Report - {datetime.now().strftime('%B %d, %Y')}"
            send_email_report(subject, email_body, csv_file)
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
