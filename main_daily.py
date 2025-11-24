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


def create_email_body(market, summary):
    """Create HTML email body with results"""
    if not summary:
        return f"""
        <h2>📊 Stock Screener - {market} Market</h2>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>⚠️ Screening completed but no results generated or CSV parsing failed.</p>
        """
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h2 {{ color: #333; }}
            .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            .strong-buy {{ color: #00aa00; font-weight: bold; }}
            .buy {{ color: #0066cc; font-weight: bold; }}
            .watch {{ color: #ff9900; }}
        </style>
    </head>
    <body>
        <h2>📊 Daily Stock Screener - {market} Market</h2>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <h3>📈 Summary</h3>
            <ul>
                <li><strong>Total Stocks:</strong> {summary['total']}</li>
                <li><span class="strong-buy">STRONG_BUY: {summary['strong_buy']}</span></li>
                <li><span class="buy">BUY: {summary['buy']}</span></li>
                <li><span class="watch">WATCH: {summary['watch']}</span></li>
            </ul>
            <p>
                <strong>Metrics:</strong><br>
                Avg P/E: {summary['avg_pe']:.2f} | Avg ROE: {summary['avg_roe']:.2f}%
            </p>
        </div>
        
        <h3>🏆 Top 10 Stocks</h3>
        <table>
            <tr>
                <th>Rank</th>
                <th>Ticker</th>
                <th>Company</th>
                <th>Action</th>
                <th>Score</th>
                <th>P/E</th>
                <th>ROE</th>
            </tr>
    """
    
    for idx, row in summary['stocks'].iterrows():
        action_class = 'strong-buy' if row['Action'] == 'STRONG_BUY' else 'buy' if row['Action'] == 'BUY' else 'watch'
        html += f"""
            <tr>
                <td>{idx + 1}</td>
                <td><strong>{row['Ticker']}</strong></td>
                <td>{row['Company']}</td>
                <td class="{action_class}">{row['Action']}</td>
                <td>{row['Composite_Score']:.1f}</td>
                <td>{row['PE_Ratio']}</td>
                <td>{row['ROE_%']}</td>
            </tr>
        """
    
    html += """
        </table>
        
        <p style="color: #666; font-size: 12px;">
            <em>Full results CSV attached. For more details, visit the GitHub repository.</em>
        </p>
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
        # Build main.py command
        cmd = ['python', 'main.py', '--market', args.market]
        if args.no_cache:
            cmd.append('--no-cache')
        
        # Run main screener
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode != 0:
            logger.error(f"❌ Screening failed with exit code {result.returncode}")
            if args.send_email:
                send_email_report(
                    subject=f"❌ Stock Screener Failed - {args.market} Market",
                    body=f"<p>The screening process failed. Please check the GitHub Actions logs for details.</p>"
                )
            sys.exit(1)
        
        logger.info("✓ Screening completed successfully")
        
        # Send email if requested
        if args.send_email:
            logger.info("📧 Preparing email report...")
            
            # Find latest CSV
            csv_file = get_latest_csv('output', args.market)
            if csv_file:
                logger.info(f"Found results: {csv_file}")
                
                # Parse summary
                summary = parse_csv_summary(csv_file)
                if summary:
                    # Create email body
                    email_body = create_email_body(args.market, summary)
                    
                    # Send email
                    subject = f"📈 Daily Stock Picks - {args.market} Market ({datetime.now().strftime('%Y-%m-%d')})"
                    send_email_report(subject, email_body, csv_file)
                else:
                    logger.warning("Could not parse CSV for email")
            else:
                logger.warning("No CSV file found to attach")
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
