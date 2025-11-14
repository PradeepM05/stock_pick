"""
Email Report Sender for Hidden Gems Stock Screener
Sends beautifully formatted HTML emails with daily results
"""
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailReporter:
    """
    Email reporter for sending daily hidden gems reports
    """
    
    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
        """
        Initialize email reporter
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        
        if not self.sender_email or not self.sender_password:
            logger.error("Email credentials not found in environment variables")
            logger.error("Set SENDER_EMAIL and SENDER_PASSWORD in .env file")
    
    def send_daily_report(self, 
                         us_results: List[Dict] = None,
                         india_results: List[Dict] = None,
                         recipients: List[str] = None,
                         attachment_files: List[str] = None) -> bool:
        """
        Send daily hidden gems report
        
        Args:
            us_results: List of US stock results
            india_results: List of India stock results  
            recipients: List of recipient email addresses
            attachment_files: List of file paths to attach
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get default recipients if none provided
            if not recipients:
                recipients = os.getenv('REPORT_RECIPIENTS', '').split(',')
                recipients = [email.strip() for email in recipients if email.strip()]
            
            if not recipients:
                logger.error("No recipients specified")
                return False
            
            # Create email message
            msg = self._create_email_message(us_results, india_results, recipients)
            
            # Attach files if provided
            if attachment_files:
                for file_path in attachment_files:
                    self._attach_file(msg, file_path)
            
            # Send email
            return self._send_email(msg, recipients)
            
        except Exception as e:
            logger.error(f"Failed to send daily report: {e}")
            return False
    
    def _create_email_message(self, 
                             us_results: List[Dict], 
                             india_results: List[Dict],
                             recipients: List[str]) -> MIMEMultipart:
        """Create formatted email message"""
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"📈 Daily Hidden Gems Report - {datetime.now().strftime('%B %d, %Y')}"
        msg['From'] = self.sender_email
        msg['To'] = ', '.join(recipients)
        
        # Generate HTML content
        html_content = self._generate_html_report(us_results, india_results)
        
        # Generate plain text version
        text_content = self._generate_text_report(us_results, india_results)
        
        # Attach both versions
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        return msg
    
    def _generate_html_report(self, us_results: List[Dict], india_results: List[Dict]) -> str:
        """Generate beautiful HTML email report"""
        
        date_str = datetime.now().strftime('%B %d, %Y')
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
        .content {{ padding: 30px; }}
        .market-section {{ margin-bottom: 40px; }}
        .market-header {{ display: flex; align-items: center; margin-bottom: 20px; }}
        .flag {{ font-size: 24px; margin-right: 10px; }}
        .market-title {{ font-size: 20px; font-weight: bold; color: #333; }}
        .summary-cards {{ display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap; }}
        .summary-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; min-width: 120px; text-align: center; border-left: 4px solid #28a745; }}
        .summary-card.strong-buy {{ border-color: #28a745; }}
        .summary-card.buy {{ border-color: #ffc107; }}
        .summary-card.speculative {{ border-color: #dc3545; }}
        .summary-card h3 {{ margin: 0; font-size: 24px; color: #333; }}
        .summary-card p {{ margin: 5px 0 0 0; color: #666; font-size: 14px; }}
        .stocks-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        .stocks-table th {{ background: #f8f9fa; padding: 12px 8px; text-align: left; border-bottom: 2px solid #dee2e6; font-weight: 600; }}
        .stocks-table td {{ padding: 10px 8px; border-bottom: 1px solid #dee2e6; }}
        .stocks-table tr:hover {{ background: #f8f9fa; }}
        .action-strong-buy {{ background: #d4edda; color: #155724; padding: 4px 8px; border-radius: 4px; font-weight: bold; }}
        .action-buy {{ background: #fff3cd; color: #856404; padding: 4px 8px; border-radius: 4px; font-weight: bold; }}
        .action-speculative {{ background: #f8d7da; color: #721c24; padding: 4px 8px; border-radius: 4px; font-weight: bold; }}
        .footer {{ background: #f8f9fa; padding: 20px 30px; border-radius: 0 0 10px 10px; text-align: center; color: #666; }}
        .no-results {{ text-align: center; padding: 20px; color: #666; background: #f8f9fa; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 Daily Hidden Gems Report</h1>
            <p>{date_str}</p>
        </div>
        
        <div class="content">
        """
        
        # US Market Section
        html += self._generate_market_section("🇺🇸", "US Market", us_results)
        
        # India Market Section  
        html += self._generate_market_section("🇮🇳", "India Market", india_results)
        
        # Footer
        html += f"""
        </div>
        
        <div class="footer">
            <p>Generated by Hidden Gems Stock Screener | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>⚠️ This is not investment advice. Always do your own research before investing.</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html
    
    def _generate_market_section(self, flag: str, title: str, results: List[Dict]) -> str:
        """Generate HTML for a market section"""
        
        if not results:
            return f"""
            <div class="market-section">
                <div class="market-header">
                    <span class="flag">{flag}</span>
                    <span class="market-title">{title}</span>
                </div>
                <div class="no-results">No results available for this market today.</div>
            </div>
            """
        
        # Count by action
        strong_buy = len([r for r in results if r.get('action') == 'STRONG_BUY'])
        buy = len([r for r in results if r.get('action') == 'BUY']) 
        speculative = len([r for r in results if r.get('action') == 'SPECULATIVE'])
        
        html = f"""
        <div class="market-section">
            <div class="market-header">
                <span class="flag">{flag}</span>
                <span class="market-title">{title}</span>
            </div>
            
            <div class="summary-cards">
                <div class="summary-card strong-buy">
                    <h3>{strong_buy}</h3>
                    <p>STRONG BUY</p>
                </div>
                <div class="summary-card buy">
                    <h3>{buy}</h3>
                    <p>BUY</p>
                </div>
                <div class="summary-card speculative">
                    <h3>{speculative}</h3>
                    <p>SPECULATIVE</p>
                </div>
                <div class="summary-card">
                    <h3>{len(results)}</h3>
                    <p>TOTAL ANALYZED</p>
                </div>
            </div>
            
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
        
        # Add top 10 stocks
        for i, stock in enumerate(results[:10], 1):
            action_class = f"action-{stock.get('action', '').lower().replace('_', '-')}"
            
            price = stock.get('current_price', 0)
            currency_symbol = '$' if 'US' in title else '₹'
            
            pe_ratio = stock.get('pe_ratio', 0)
            pe_display = f"{pe_ratio:.1f}" if pe_ratio else 'N/A'
            
            roe = stock.get('roe', 0)
            roe_display = f"{roe:.1f}%" if roe else 'N/A'
            
            score = stock.get('composite_score', 0)
            
            html += f"""
                    <tr>
                        <td>{i}</td>
                        <td><strong>{stock.get('ticker', 'N/A')}</strong></td>
                        <td>{stock.get('company_name', 'N/A')[:30]}{'...' if len(stock.get('company_name', '')) > 30 else ''}</td>
                        <td>{currency_symbol}{price:.2f}</td>
                        <td>{pe_display}</td>
                        <td>{roe_display}</td>
                        <td>{score:.1f}</td>
                        <td><span class="{action_class}">{stock.get('action', 'N/A')}</span></td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
        
        return html
    
    def _generate_text_report(self, us_results: List[Dict], india_results: List[Dict]) -> str:
        """Generate plain text version of the report"""
        
        date_str = datetime.now().strftime('%B %d, %Y')
        
        text = f"""📈 DAILY HIDDEN GEMS REPORT - {date_str}
{'=' * 60}

"""
        
        # US Section
        text += "🇺🇸 US MARKET\n"
        text += "-" * 20 + "\n"
        if us_results:
            strong_buy = len([r for r in us_results if r.get('action') == 'STRONG_BUY'])
            buy = len([r for r in us_results if r.get('action') == 'BUY'])
            speculative = len([r for r in us_results if r.get('action') == 'SPECULATIVE'])
            
            text += f"STRONG_BUY: {strong_buy} | BUY: {buy} | SPECULATIVE: {speculative}\n"
            text += f"Total Analyzed: {len(us_results)}\n\n"
            
            text += "TOP 5 US PICKS:\n"
            for i, stock in enumerate(us_results[:5], 1):
                text += f"{i}. {stock.get('ticker')} - {stock.get('company_name', '')[:40]}\n"
                text += f"   ${stock.get('current_price', 0):.2f} | P/E: {stock.get('pe_ratio', 'N/A')} | Score: {stock.get('composite_score', 0):.1f} | {stock.get('action', 'N/A')}\n\n"
        else:
            text += "No US results available today.\n\n"
        
        # India Section
        text += "🇮🇳 INDIA MARKET\n"
        text += "-" * 20 + "\n"
        if india_results:
            strong_buy = len([r for r in india_results if r.get('action') == 'STRONG_BUY'])
            buy = len([r for r in india_results if r.get('action') == 'BUY'])
            speculative = len([r for r in india_results if r.get('action') == 'SPECULATIVE'])
            
            text += f"STRONG_BUY: {strong_buy} | BUY: {buy} | SPECULATIVE: {speculative}\n"
            text += f"Total Analyzed: {len(india_results)}\n\n"
            
            text += "TOP 5 INDIA PICKS:\n"
            for i, stock in enumerate(india_results[:5], 1):
                text += f"{i}. {stock.get('ticker')} - {stock.get('company_name', '')[:40]}\n"
                text += f"   ₹{stock.get('current_price', 0):.2f} | P/E: {stock.get('pe_ratio', 'N/A')} | Score: {stock.get('composite_score', 0):.1f} | {stock.get('action', 'N/A')}\n\n"
        else:
            text += "No India results available today.\n\n"
        
        text += "⚠️ This is not investment advice. Always do your own research before investing.\n"
        text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return text
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Attach file to email"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.warning(f"Attachment file not found: {file_path}")
                return
            
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {file_path.name}'
            )
            
            msg.attach(part)
            logger.info(f"Attached file: {file_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to attach file {file_path}: {e}")
    
    def _send_email(self, msg: MIMEMultipart, recipients: List[str]) -> bool:
        """Send the email"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            
            text = msg.as_string()
            server.sendmail(self.sender_email, recipients, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_error_notification(self, error_message: str, recipients: List[str] = None) -> bool:
        """Send error notification email"""
        try:
            if not recipients:
                recipients = os.getenv('REPORT_RECIPIENTS', '').split(',')
                recipients = [email.strip() for email in recipients if email.strip()]
            
            if not recipients:
                return False
            
            msg = MIMEMultipart()
            msg['Subject'] = f"❌ Hidden Gems Screener Error - {datetime.now().strftime('%Y-%m-%d')}"
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(recipients)
            
            body = f"""
❌ Hidden Gems Stock Screener Error Report

The daily stock screening failed with the following error:

{error_message}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check the system and try running manually.

---
Automated Error Notification System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            return self._send_email(msg, recipients)
            
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
            return False