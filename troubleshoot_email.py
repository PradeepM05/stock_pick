#!/usr/bin/env python3
"""
Stock Screener Email Troubleshooting Script
Run this to diagnose and test your email system
"""
import os
import sys
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from src.utils import load_env_vars
    print("✓ Successfully imported utils")
except ImportError as e:
    print(f"❌ Error importing utils: {e}")
    sys.exit(1)


def test_environment_variables():
    """Test if environment variables are properly configured"""
    print("\n=== ENVIRONMENT VARIABLES TEST ===")
    
    env_vars = load_env_vars()
    
    # Required variables for email
    required_vars = {
        'sender_email': 'SENDER_EMAIL',
        'sender_password': 'SENDER_PASSWORD', 
        'report_recipients': 'REPORT_RECIPIENTS'
    }
    
    all_good = True
    
    for var_key, env_name in required_vars.items():
        value = env_vars.get(var_key)
        if value:
            if var_key == 'sender_password':
                print(f"✓ {env_name}: Set (length: {len(value)} chars)")
            else:
                print(f"✓ {env_name}: {value}")
        else:
            print(f"❌ {env_name}: NOT SET")
            all_good = False
    
    # Check if recipients can be parsed
    if env_vars.get('report_recipients'):
        recipients = env_vars.get('report_recipients', '').split(',')
        recipients = [email.strip() for email in recipients if email.strip()]
        print(f"✓ Parsed recipients: {recipients} (count: {len(recipients)})")
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for email in recipients:
            if re.match(email_pattern, email):
                print(f"✓ Valid email format: {email}")
            else:
                print(f"❌ Invalid email format: {email}")
                all_good = False
    
    return all_good


def test_csv_files():
    """Check for CSV files in output directory"""
    print("\n=== CSV FILES TEST ===")
    
    output_path = Path('output')
    
    if not output_path.exists():
        print(f"❌ Output directory does not exist: {output_path}")
        return False
    
    print(f"✓ Output directory exists: {output_path}")
    
    # List all files
    all_files = list(output_path.glob('*'))
    csv_files = list(output_path.glob('*.csv'))
    
    print(f"Total files in output/: {len(all_files)}")
    print(f"CSV files found: {len(csv_files)}")
    
    if all_files:
        print("All files:")
        for f in all_files:
            print(f"  - {f.name}")
    
    if csv_files:
        print("CSV files:")
        for f in csv_files:
            size_mb = f.stat().st_size / (1024*1024)
            print(f"  - {f.name} ({size_mb:.2f} MB)")
        
        # Test parsing the latest CSV
        latest_csv = max(csv_files, key=os.path.getctime)
        print(f"\nTesting latest CSV: {latest_csv.name}")
        
        try:
            import pandas as pd
            df = pd.read_csv(latest_csv)
            print(f"✓ CSV loaded successfully: {len(df)} rows, {len(df.columns)} columns")
            print(f"  Columns: {list(df.columns)}")
            
            # Check for common action columns
            action_columns = ['Action', 'Rating', 'Recommendation', 'Signal']
            found_action = None
            for col in action_columns:
                if col in df.columns:
                    found_action = col
                    break
            
            if found_action:
                print(f"✓ Found action column: {found_action}")
                print(f"  Unique values: {df[found_action].value_counts().to_dict()}")
            else:
                print("❌ No standard action column found")
            
            return True
            
        except Exception as e:
            print(f"❌ Error parsing CSV: {e}")
            return False
    else:
        print("❌ No CSV files found")
        return False


def test_email_connection():
    """Test SMTP connection without sending email"""
    print("\n=== EMAIL CONNECTION TEST ===")
    
    env_vars = load_env_vars()
    sender_email = env_vars.get('sender_email')
    sender_password = env_vars.get('sender_password')
    
    if not sender_email or not sender_password:
        print("❌ Email credentials not configured")
        return False
    
    try:
        print("Testing SMTP connection to gmail.com:587...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        print("✓ TLS connection established")
        
        server.login(sender_email, sender_password)
        print("✓ Authentication successful")
        
        server.quit()
        print("✓ Connection closed properly")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed - Check your email and app password")
        print("   Make sure you're using an App Password, not your regular Gmail password")
        return False
    except smtplib.SMTPConnectError:
        print("❌ Could not connect to SMTP server")
        return False
    except Exception as e:
        print(f"❌ SMTP error: {e}")
        return False


def send_test_email():
    """Send a simple test email"""
    print("\n=== TEST EMAIL SEND ===")
    
    env_vars = load_env_vars()
    sender_email = env_vars.get('sender_email')
    sender_password = env_vars.get('sender_password')
    recipients = env_vars.get('report_recipients', '').split(',')
    recipients = [email.strip() for email in recipients if email.strip()]
    
    if not sender_email or not sender_password or not recipients:
        print("❌ Email configuration incomplete")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = "🧪 Stock Screener Email Test"
        
        body = """
        <html>
        <body>
        <h2>Email Test Successful! ✅</h2>
        <p>This is a test email from your stock screener system.</p>
        <p>If you received this, your email configuration is working correctly.</p>
        <p><strong>Test timestamp:</strong> {}</p>
        </body>
        </html>
        """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print(f"✓ Test email sent successfully to {len(recipients)} recipient(s)")
        print(f"  Recipients: {recipients}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending test email: {e}")
        return False


def run_main_script_test():
    """Test running the main script"""
    print("\n=== MAIN SCRIPT TEST ===")
    
    import subprocess
    
    # Test if main.py can be imported
    try:
        cmd = ['python', '-c', 'import main; print("✓ main.py can be imported")']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✓ main.py imports successfully")
        else:
            print(f"❌ main.py import failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ main.py import timeout")
        return False
    except Exception as e:
        print(f"❌ Error testing main.py: {e}")
        return False
    
    # Test help command
    try:
        cmd = ['python', 'main.py', '--help']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✓ main.py --help works")
        else:
            print(f"❌ main.py --help failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing main.py --help: {e}")
        return False
    
    return True


def main():
    """Run all tests"""
    from datetime import datetime
    
    print("🔍 STOCK SCREENER EMAIL TROUBLESHOOTING")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("CSV Files", test_csv_files),
        ("Email Connection", test_email_connection),
        ("Main Script", run_main_script_test)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name} test...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Your email system should be working.")
        
        # Offer to send test email
        response = input("\nWould you like to send a test email? (y/n): ")
        if response.lower() == 'y':
            send_test_email()
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\n📋 Common fixes:")
        print("1. Set up Gmail App Password (not regular password)")
        print("2. Check environment variables in .env file")
        print("3. Make sure CSV files are being generated")
        print("4. Check GitHub Actions secrets")


if __name__ == '__main__':
    main()