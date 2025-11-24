# GitHub Actions Setup Guide

## Issue Found & Fixed

Your GitHub Actions workflow was failing because:
- ❌ The workflow called `main_daily.py` but it didn't exist
- ❌ Better error handling was needed

### What I Fixed

1. **Created `main_daily.py`** - GitHub Actions entry point that:
   - Runs the main screener (`main.py`)
   - Sends email reports with results (optional)
   - Handles errors gracefully
   - Attaches CSV results to emails

2. **Updated `.github/workflows/daily-screener.yml`** to:
   - Better handle missing output files
   - Improved logging and summary generation
   - Fixed file path patterns

## GitHub Secrets Configuration

For the workflow to send emails, configure these GitHub Secrets:

Go to: **Settings → Secrets and variables → Actions**

Add these secrets:

```
SENDER_EMAIL          = your-email@gmail.com
SENDER_PASSWORD       = your-app-password (NOT your regular password)
REPORT_RECIPIENTS     = recipient1@email.com,recipient2@email.com
YAHOO_FINANCE_API_KEY = your-api-key (optional, already in .env)
```

### Getting Gmail App Password

1. Enable 2-Step Verification on your Google Account
2. Go to https://myaccount.google.com/apppasswords
3. Generate an "App password" for "Mail" and "Windows"
4. Use this password in `SENDER_PASSWORD` secret (16-character code)

## Workflow Schedule

The workflow runs automatically:
- **6:30 PM EST (23:30 UTC)** - US market screening (Monday-Friday)
- **4:00 PM IST (10:30 UTC)** - India market screening (Monday-Friday)

## Manual Trigger

To run manually:
1. Go to Actions → Daily Hidden Gems Screener
2. Click "Run workflow"
3. Select market (US, INDIA, or BOTH)
4. Choose whether to send email report

## Files Involved

- `main_daily.py` - GitHub Actions entry point (NEW)
- `main.py` - Core screener logic
- `.github/workflows/daily-screener.yml` - Workflow configuration
- `.env` - Environment variables (configure locally)

## Debugging

Check workflow logs at:
https://github.com/PradeepM05/stock_pick/actions

Look at the "Run stock screening" step for errors.

---

**Status:** ✅ Ready to deploy
