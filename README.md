# Stock Screener v2.0

A professional stock screening application for US and Indian markets with intelligent caching, multiple data sources, and clean architecture.

## 🚀 Features

- **Multi-Market Support**: Screen stocks from US (NYSE, NASDAQ) and Indian (NSE, BSE) markets
- **Multiple Data Sources**: Yahoo Finance API, NSE India, YFinance screener (with automatic fallback)
- **Smart Caching**: Configurable caching to reduce API calls and improve performance
- **Flexible Filtering**: Comprehensive filtering by market cap, P/E ratio, ROE, debt-to-equity, and more
- **Clean Architecture**: Well-organized, modular, and easily extensible codebase
- **Production Ready**: Proper logging, error handling, and configuration management

## 📁 Project Structure

```
stock-screener/
│
├── src/
│   ├── config/              # Configuration files
│   │   ├── settings.py      # Base settings
│   │   ├── us_config.py     # US market config
│   │   └── india_config.py  # India market config
│   │
│   ├── screeners/           # Screening logic
│   │   ├── base_screener.py
│   │   ├── us_screener.py
│   │   └── india_screener.py
│   │
│   ├── data/                # Data fetching & caching
│   │   ├── api_client.py
│   │   └── cache_manager.py
│   │
│   └── utils/               # Utilities
│       ├── logger.py
│       └── helpers.py
│
├── output/                  # Output files
├── cache/                   # Cache directory
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
└── .env.example            # Environment variables template
```

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd stock-screener
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup environment variables**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## 🔑 API Keys

### Yahoo Finance API (Recommended for full functionality)
1. Go to [yfapi.net](https://yfapi.net/)
2. Sign up for a free account
3. Get your API key
4. Add to `.env`: `YAHOO_FINANCE_API_KEY=your_key_here`

**Note**: The application works without an API key using fallback methods, but with limited functionality.

## 🚀 Usage

### Basic Usage

**Screen US stocks:**
```bash
python main.py --market US
```

**Screen Indian stocks:**
```bash
python main.py --market INDIA
```

**Screen both markets:**
```bash
python main.py --market BOTH
```

### Advanced Options

**Disable cache (force fresh data):**
```bash
python main.py --market US --no-cache
```

**Clear cache before running:**
```bash
python main.py --market US --clear-cache
```

**Set logging level:**
```bash
python main.py --market US --log-level DEBUG
```

**Save results to file:**
```bash
python main.py --market US --output output/my_stocks.txt
```

## ⚙️ Configuration

### Market Filters

Edit `src/config/us_config.py` or `src/config/india_config.py` to customize filters:

```python
US_FILTERS = {
    'market_cap_min': 300_000_000,      # $300M
    'market_cap_max': 10_000_000_000,   # $10B
    'volume_min': 500_000,
    'pe_ratio_max': 30,
    'roe_min': 12,
    'debt_to_equity_max': 2.0,
    'revenue_growth_min': 10,
    'earnings_growth_min': 8,
    # ... more filters
}
```

### Cache Settings

Modify cache behavior in `src/config/settings.py`:

```python
CACHE_CONFIG = {
    'enabled': True,
    'duration_hours': 24,
    'refresh_frequency': 'daily',
}
```

## 📊 Output

The screener outputs:
- List of stock tickers matching your criteria
- Number of stocks found per market
- Optional file export with ticker list

Example output:
```
======================================================================
Screening US Market
======================================================================
✓ US (Yahoo API): Found 247 stocks
Applied filters: 247 stocks remaining
✓ Saved 247 tickers to cache

======================================================================
RESULTS
======================================================================
Found 247 stocks

Showing first 20 of 247 stocks:
   1. AAPL
   2. MSFT
   3. GOOGL
   ...
```

## 🏗️ Architecture

### Screener Pattern
- **BaseScreener**: Abstract base class
- **USScreener**: US market implementation
- **IndiaScreener**: India market implementation
- Easy to add new markets by inheriting from BaseScreener

### Data Sources with Fallback
1. **Primary**: Yahoo Finance API (requires key)
2. **Secondary**: NSE India (for Indian stocks) or YFinance Screener (for US stocks)
3. **Automatic fallback** if primary source fails

### Caching Strategy
- Pickle-based caching with timestamp
- Configurable cache duration
- Per-market cache files
- Cache info and clearing utilities

## 🔧 Development

### Adding a New Market

1. Create config in `src/config/`:
```python
# new_market_config.py
NEW_MARKET_FILTERS = {...}
NEW_MARKET_CONFIG = {...}
```

2. Create screener in `src/screeners/`:
```python
# new_market_screener.py
class NewMarketScreener(BaseScreener):
    def get_market_name(self):
        return 'NEW_MARKET'
    # ... implement required methods
```

3. Update factory function in `src/screeners/__init__.py`

### Running Tests
```bash
# Coming soon
python -m pytest tests/
```

## 📝 TODO

- [ ] Add fundamental analysis module
- [ ] Add technical analysis module
- [ ] Add scoring system
- [ ] Export to CSV/Excel with detailed data
- [ ] Add unit tests
- [ ] Add web interface
- [ ] Add portfolio tracking
- [ ] Add alerts and notifications

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - Feel free to use this project for personal or commercial purposes.

## 🙏 Acknowledgments

- Yahoo Finance for market data
- NSE India for Indian market data
- YFinance library for Python wrapper

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact: [your-email@example.com]

---

**Happy Screening! 📈**
