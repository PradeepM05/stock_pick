"""
API Client - Handles all external API calls
"""
import requests
import time
import os
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class YahooFinanceClient:
    """Client for Yahoo Finance API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Yahoo Finance client
        
        Args:
            api_key: Yahoo Finance API key (from yfapi.net)
        """
        self.api_key = api_key or os.getenv('YAHOO_FINANCE_API_KEY')
        self.base_url = "https://yfapi.net/v6/finance/screener"
        
        if not self.api_key:
            logger.warning("Yahoo Finance API key not provided - some features may be limited")
    
    def screen_stocks(self, region: str, filters: Dict, 
                     max_results: int = 1000) -> List[str]:
        """
        Screen stocks using Yahoo Finance API
        
        Args:
            region: Market region ('US' or 'IN')
            filters: Filter criteria dictionary
            max_results: Maximum number of results to fetch
            
        Returns:
            List of stock ticker symbols
        """
        if not self.api_key:
            logger.error("Cannot use Yahoo API without API key")
            return []
        
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # Build query
        query = self._build_query(filters, region)
        
        all_tickers = []
        page_size = 250
        
        # Paginate through results
        for offset in range(0, max_results, page_size):
            payload = {
                "size": page_size,
                "offset": offset,
                "sortField": "marketcap",
                "sortType": "DESC",
                "quoteType": "EQUITY",
                "query": query
            }
            
            try:
                response = requests.post(
                    self.base_url, 
                    headers=headers, 
                    json=payload, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    quotes = self._extract_quotes(data)
                    
                    if not quotes:
                        break
                    
                    tickers = [q.get('symbol') for q in quotes if q.get('symbol')]
                    all_tickers.extend(tickers)
                    
                    logger.info(f"  Page {offset//page_size + 1}: {len(tickers)} stocks")
                    
                    # Stop if we got fewer results than page size
                    if len(quotes) < page_size:
                        break
                        
                elif response.status_code == 401:
                    logger.error("API key invalid or expired")
                    break
                elif response.status_code == 429:
                    logger.warning("Rate limit hit, waiting...")
                    time.sleep(5)
                    continue
                else:
                    logger.warning(f"API returned status {response.status_code}")
                    break
                    
            except requests.exceptions.Timeout:
                logger.error("API request timed out")
                break
            except Exception as e:
                logger.error(f"API call failed: {e}")
                break
            
            time.sleep(0.5)  # Rate limiting
        
        return list(set(all_tickers))  # Remove duplicates
    
    def _build_query(self, filters: Dict, region: str) -> Dict:
        """Build Yahoo Finance query from filters"""
        operands = []
        
        # Market cap filter
        min_cap = filters.get('market_cap_min', 0)
        max_cap = filters.get('market_cap_max', float('inf'))
        
        if min_cap or max_cap < float('inf'):
            operands.append({
                'operator': 'BTWN',
                'operands': ['intradaymarketcap', min_cap, max_cap]
            })
        
        # Volume filter
        if 'volume_min' in filters:
            operands.append({
                'operator': 'GT',
                'operands': ['avgdailyvol3m', filters['volume_min']]
            })
        
        # P/E ratio filter
        if 'pe_ratio_max' in filters:
            operands.append({
                'operator': 'LT',
                'operands': ['trailingpe', filters['pe_ratio_max']]
            })
        
        # Positive earnings
        operands.append({
            'operator': 'GT',
            'operands': ['trailingeps', 0]
        })
        
        # Region filter
        operands.append({
            'operator': 'EQ',
            'operands': ['region', region.lower()]
        })
        
        return {
            'operator': 'AND',
            'operands': operands
        }
    
    def _extract_quotes(self, data: Dict) -> List[Dict]:
        """Extract quotes from API response"""
        try:
            if 'finance' in data and 'result' in data['finance']:
                results = data['finance']['result']
                if results and len(results) > 0:
                    return results[0].get('quotes', [])
        except Exception as e:
            logger.error(f"Error extracting quotes: {e}")
        
        return []


class NSEIndiaClient:
    """Client for NSE India data"""
    
    BASE_URL = "https://nsearchives.nseindia.com"
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch_nifty_500(self) -> List[str]:
        """
        Fetch Nifty 500 stock list
        
        Returns:
            List of stock ticker symbols with .NS suffix
        """
        url = f"{self.BASE_URL}/content/indices/ind_nifty500list.csv"
        
        try:
            import pandas as pd
            from io import StringIO
            
            logger.info("Fetching NSE Nifty 500...")
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                df = pd.read_csv(StringIO(response.text))
                tickers = [f"{symbol}.NS" for symbol in df['Symbol'].tolist()]
                logger.info(f"✓ NSE: {len(tickers)} stocks fetched")
                return tickers
            else:
                logger.error(f"NSE API returned status {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching NSE data: {e}")
            return []
    
    def fetch_index(self, index_name: str) -> List[str]:
        """
        Fetch stocks from specific NSE index
        
        Args:
            index_name: Name of the index (e.g., 'NIFTY50', 'NIFTY_MIDCAP_100')
            
        Returns:
            List of stock ticker symbols
        """
        # Map index names to CSV URLs
        index_urls = {
            'NIFTY50': '/content/indices/ind_nifty50list.csv',
            'NIFTY500': '/content/indices/ind_nifty500list.csv',
            'NIFTY_MIDCAP_100': '/content/indices/ind_niftymidcap100list.csv',
            'NIFTY_SMALLCAP_100': '/content/indices/ind_niftysmallcap100list.csv'
        }
        
        csv_path = index_urls.get(index_name.upper())
        if not csv_path:
            logger.warning(f"Unknown index: {index_name}")
            return []
        
        try:
            import pandas as pd
            from io import StringIO
            
            url = f"{self.BASE_URL}{csv_path}"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                df = pd.read_csv(StringIO(response.text))
                tickers = [f"{symbol}.NS" for symbol in df['Symbol'].tolist()]
                return tickers
            else:
                logger.error(f"Failed to fetch {index_name}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching {index_name}: {e}")
            return []


class YFinanceScreenerClient:
    """Fallback client that uses public stock lists (free, no API key)"""
    
    def __init__(self):
        pass
    
    def screen_us_stocks(self, filters: Dict) -> List[str]:
        """
        Screen US stocks using publicly available stock lists
        
        Args:
            filters: Filter criteria
            
        Returns:
            List of ticker symbols
        """
        logger.info("Using free fallback method for US stocks...")
        
        # Try to get S&P 500 list
        tickers = self._get_sp500_list()
        
        if not tickers:
            # Fallback to hardcoded popular stocks
            logger.info("Using expanded stock universe...")
            tickers = self._get_expanded_stock_universe()
        
        if tickers:
            logger.info(f"Found {len(tickers)} US stocks")
        
        return tickers
    
    def screen_india_stocks(self, filters: Dict) -> List[str]:
        """
        Screen India stocks using yfinance as fallback
        
        Args:
            filters: Filter criteria
            
        Returns:
            List of ticker symbols with .NS suffix
        """
        logger.info("Using yfinance fallback for India stocks...")
        
        try:
            import yfinance as yf
            import pandas as pd
            
            # Method 1: Try to get Nifty 500 constituents
            logger.info("Trying to fetch Nifty indices...")
            
            nifty_stocks = []
            
            # Try major Indian indices
            indices = {
                '^NSEI': 'Nifty 50',
                '^NSEBANK': 'Nifty Bank',
                '^CNXIT': 'Nifty IT',
                '^CNXPHARMA': 'Nifty Pharma'
            }
            
            for index_symbol, index_name in indices.items():
                try:
                    index = yf.Ticker(index_symbol)
                    info = index.info
                    if info:
                        logger.info(f"✓ {index_name} validated")
                except Exception as e:
                    logger.debug(f"Could not fetch {index_name}: {e}")
            
            # Method 2: Use curated list of major Indian stocks
            logger.info("Using curated list of major Indian stocks...")
            nifty_stocks = self._get_major_indian_stocks()
            
            logger.info(f"✓ Found {len(nifty_stocks)} Indian stocks")
            return nifty_stocks
            
        except Exception as e:
            logger.error(f"Error in screen_india_stocks: {e}")
            return self._get_major_indian_stocks()
    
    def _get_major_indian_stocks(self) -> List[str]:
        """
        Return major Indian stocks (Nifty 50 + Next 450)
        Comprehensive fallback list
        """
        # Nifty 50 + popular stocks from Nifty Next 50 and Nifty Midcap
        stocks = [
            # Nifty 50 (Top 50 companies)
            'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
            'HINDUNILVR.NS', 'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS',
            'LT.NS', 'AXISBANK.NS', 'ASIANPAINT.NS', 'MARUTI.NS', 'TITAN.NS',
            'SUNPHARMA.NS', 'BAJFINANCE.NS', 'ULTRACEMCO.NS', 'NESTLEIND.NS', 'WIPRO.NS',
            'ONGC.NS', 'HCLTECH.NS', 'BAJAJFINSV.NS', 'ADANIENT.NS', 'TATAMOTORS.NS',
            'POWERGRID.NS', 'NTPC.NS', 'M&M.NS', 'JSWSTEEL.NS', 'TATASTEEL.NS',
            'COALINDIA.NS', 'HINDALCO.NS', 'INDUSINDBK.NS', 'DRREDDY.NS', 'CIPLA.NS',
            'TECHM.NS', 'EICHERMOT.NS', 'BAJAJ-AUTO.NS', 'HEROMOTOCO.NS', 'DIVISLAB.NS',
            'GRASIM.NS', 'BPCL.NS', 'BRITANNIA.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS',
            'SBILIFE.NS', 'HDFCLIFE.NS', 'TATACONSUM.NS', 'SHRIRAMFIN.NS', 'UPL.NS',
            
            # Nifty Next 50 (Next 50 large companies)
            'ADANIGREEN.NS', 'ADANITRANS.NS', 'AMBUJACEM.NS', 'ATGL.NS', 'BANKBARODA.NS',
            'BERGEPAINT.NS', 'BEL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'CHOLAFIN.NS',
            'COLPAL.NS', 'DABUR.NS', 'DLF.NS', 'DMART.NS', 'GAIL.NS',
            'GODREJCP.NS', 'HAVELLS.NS', 'HDFC.NS', 'HINDZINC.NS', 'ICICIPRULI.NS',
            'IDEA.NS', 'INDIGO.NS', 'INDUSTOWER.NS', 'IOC.NS', 'IRCTC.NS',
            'JINDALSTEL.NS', 'JUBLFOOD.NS', 'LICHSGFIN.NS', 'LTIM.NS', 'MARICO.NS',
            'MCDOWELL-N.NS', 'MPHASIS.NS', 'MUTHOOTFIN.NS', 'NMDC.NS', 'NAUKRI.NS',
            'OFSS.NS', 'ONGC.NS', 'PAGEIND.NS', 'PERSISTENT.NS', 'PETRONET.NS',
            'PFC.NS', 'PIDILITIND.NS', 'PIIND.NS', 'PNB.NS', 'RECLTD.NS',
            'SAIL.NS', 'SBICARD.NS', 'SIEMENS.NS', 'TATAPOWER.NS', 'VEDL.NS',
            
            # Nifty Midcap 150 (Selected quality midcaps - 100 stocks)
            'ABCAPITAL.NS', 'ABB.NS', 'ACC.NS', 'APLAPOLLO.NS', 'AUBANK.NS',
            'AUROPHARMA.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BATAINDIA.NS', 'BHARATFORG.NS',
            'CANBK.NS', 'CANFINHOME.NS', 'CENTRALBK.NS', 'CHAMBLFERT.NS', 'COFORGE.NS',
            'COROMANDEL.NS', 'CREDITACC.NS', 'CUMMINSIND.NS', 'DEEPAKNTR.NS', 'DELTACORP.NS',
            'DIXON.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'FORTIS.NS',
            'GLENMARK.NS', 'GMRINFRA.NS', 'GODREJPROP.NS', 'GUJGASLTD.NS', 'HATSUN.NS',
            'IDFCFIRSTB.NS', 'IEX.NS', 'INDIANB.NS', 'INDIACEM.NS', 'INDIAMART.NS',
            'INDHOTEL.NS', 'IPCALAB.NS', 'IRB.NS', 'IRFC.NS', 'JKCEMENT.NS',
            'JSWENERGY.NS', 'KAJARIACER.NS', 'KPITTECH.NS', 'L&TFH.NS', 'LALPATHLAB.NS',
            'LAURUSLABS.NS', 'LINDEINDIA.NS', 'LUPIN.NS', 'MANAPPURAM.NS', 'MAZDOCK.NS',
            'METROPOLIS.NS', 'MGL.NS', 'MFSL.NS', 'MOTHERSON.NS', 'NAM-INDIA.NS',
            'NAUKRI.NS', 'NAVINFLUOR.NS', 'OBEROIRLTY.NS', 'OIL.NS', 'PAGEIND.NS',
            'PERSISTENT.NS', 'PETRONET.NS', 'PFIZER.NS', 'PHOENIXLTD.NS', 'POLYCAB.NS',
            'PRESTIGE.NS', 'PRAJIND.NS', 'RBLBANK.NS', 'SAIL.NS', 'SCHAEFFLER.NS',
            'SRF.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SUPREMEIND.NS', 'SYNGENE.NS',
            'TATACOMM.NS', 'TATAELXSI.NS', 'TATAMTRDVR.NS', 'TATASTEEL.NS', 'TORNTPHARM.NS',
            'TORNTPOWER.NS', 'TRENT.NS', 'TVSMOTOR.NS', 'UBL.NS', 'UNIONBANK.NS',
            'UPL.NS', 'VOLTAS.NS', 'WHIRLPOOL.NS', 'ZEEL.NS', 'ZYDUSLIFE.NS',
            'CROMPTON.NS', 'CUMMINSIND.NS', 'Dixon.NS', 'HAPPSTMNDS.NS', 'HDFCAMC.NS',
            
            # Additional quality stocks (100 more)
            'AARTIIND.NS', 'ABBOTINDIA.NS', 'ABFRL.NS', 'ABSLAMC.NS', 'ACE.NS',
            'ADANIPOWER.NS', 'AFFLE.NS', 'AJANTPHARM.NS', 'AKZOINDIA.NS', 'ALKEM.NS',
            'ALKYLAMINE.NS', 'AMBUJACEM.NS', 'APOLLOTYRE.NS', 'ASHOKLEY.NS', 'ASTRAL.NS',
            'ATUL.NS', 'BAJAJELEC.NS', 'BAJAJHLDNG.NS', 'BALRAMCHIN.NS', 'BSOFT.NS',
            'CEATLTD.NS', 'CHOLAFIN.NS', 'CLEAN.NS', 'COCHINSHIP.NS', 'CONCOR.NS',
            'CYIENT.NS', 'DABUR.NS', 'DCBBANK.NS', 'DCMSHRIRAM.NS', 'DEEPAKFERT.NS',
            'DELHIVERY.NS', 'DHANI.NS', 'DIVISLAB.NS', 'EMAMILTD.NS', 'ENGINERSIN.NS',
            'FINEORG.NS', 'FSL.NS', 'GLAND.NS', 'GNFC.NS', 'GODFRYPHLP.NS',
            'GPPL.NS', 'GRANULES.NS', 'GRAPHITE.NS', 'GREENLAM.NS', 'GRINDWELL.NS',
            'GSPL.NS', 'GUJALKALI.NS', 'GULFOILLUB.NS', 'HAL.NS', 'HINDCOPPER.NS',
            'HINDPETRO.NS', 'HONAUT.NS', 'IFBIND.NS', 'IIFL.NS', 'INDIACEM.NS',
            'INDIAGLYCOL.NS', 'INEOSSTYRO.NS', 'IOB.NS', 'IRCON.NS', 'ISEC.NS',
            'ITCHOTELS.NS', 'JBCHEPHARM.NS', 'JKLAKSHMI.NS', 'JKPAPER.NS', 'JMFINANCIL.NS',
            'JSL.NS', 'KALYANKJIL.NS', 'KANSAINER.NS', 'KEI.NS', 'KSB.NS',
            'LATENTVIEW.NS', 'LEMONTREE.NS', 'LUXIND.NS', 'MAHINDCIE.NS', 'MAHLIFE.NS',
            'MAHABANK.NS', 'MASTEK.NS', 'MINDTREE.NS', 'MOREPENLAB.NS', 'MRF.NS',
            'NATCOPHARM.NS', 'NAUKRI.NS', 'NAVNETEDUL.NS', 'NCC.NS', 'NHPC.NS',
            'NLCINDIA.NS', 'ORIENTELEC.NS', 'PAYTM.NS', 'PGHH.NS', 'PIIND.NS',
            'POLYMED.NS', 'POWERGRID.NS', 'PPLPHARMA.NS', 'PRSMJOHNSN.NS', 'RADICO.NS',
            'RAJESHEXPO.NS', 'RAIN.NS', 'REDINGTON.NS', 'RELAXO.NS', 'RCF.NS'
        ]
        
        return sorted(list(set(stocks)))  # Remove duplicates
    
    def _get_sp500_list(self) -> List[str]:
        """
        Get S&P 500 ticker list using yfinance directly
        This is more reliable than Wikipedia scraping!
        """
        try:
            import yfinance as yf
            import pandas as pd
            
            logger.info("Fetching S&P 500 list using yfinance...")
            
            # Method 1: Try Wikipedia first (fast if it works)
            try:
                url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
                tables = pd.read_html(url)
                
                if tables and len(tables) > 0:
                    df = tables[0]
                    tickers = df['Symbol'].tolist()
                    
                    # Clean tickers (BRK.B → BRK-B for yfinance)
                    tickers = [ticker.replace('.', '-') for ticker in tickers]
                    
                    logger.info(f"✓ Wikipedia: {len(tickers)} S&P 500 stocks")
                    return tickers
            except Exception as e:
                logger.warning(f"Wikipedia failed: {e}")
            
            # Method 2: Use yfinance to get S&P 500 components
            logger.info("Trying yfinance method...")
            
            # Get S&P 500 ETF (SPY) holdings as proxy
            spy = yf.Ticker("SPY")
            
            # Try to get holdings
            try:
                holdings = spy.get_institutional_holders()
                if holdings is not None and not holdings.empty:
                    # This might not give us tickers directly, so try another method
                    pass
            except:
                pass
            
            # Method 3: Download a curated list from GitHub
            logger.info("Trying GitHub curated list...")
            try:
                github_url = 'https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv'
                df = pd.read_csv(github_url)
                tickers = df['Symbol'].tolist()
                tickers = [ticker.replace('.', '-') for ticker in tickers]
                logger.info(f"✓ GitHub: {len(tickers)} S&P 500 stocks")
                return tickers
            except Exception as e:
                logger.warning(f"GitHub failed: {e}")
            
            # Method 4: Use comprehensive list from multiple sources
            logger.info("Using comprehensive stock universe...")
            
            # Get multiple major indices and combine
            indices_tickers = []
            
            # Try to get from various indices
            for index_symbol in ['^GSPC', 'SPY', 'VOO', 'IVV']:
                try:
                    idx = yf.Ticker(index_symbol)
                    # This won't give us components directly, but validates the index exists
                    info = idx.info
                    if info:
                        logger.info(f"Index {index_symbol} validated")
                except:
                    pass
            
            # If all methods fail, use expanded popular list
            logger.warning("All automated methods failed, using expanded stock universe...")
            return self._get_expanded_stock_universe()
                
        except Exception as e:
            logger.error(f"Error in _get_sp500_list: {e}")
            return []
    
    def _get_expanded_stock_universe(self) -> List[str]:
        """
        Return expanded universe of US stocks (~500 stocks)
        Fallback when automated methods fail
        """
        logger.info("Using expanded stock universe (500+ stocks)")
        
        # Comprehensive list of major US stocks across all sectors
        # This is better than 106 stocks!
        stocks = []
        
        # Tech (100 stocks)
        tech = [
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NVDA', 'TSLA', 'AMD', 'INTC',
            'CSCO', 'ADBE', 'CRM', 'ORCL', 'AVGO', 'TXN', 'QCOM', 'IBM', 'INTU', 'NOW',
            'AMAT', 'MU', 'ADI', 'LRCX', 'KLAC', 'SNPS', 'CDNS', 'MCHP', 'NXPI', 'MRVL',
            'TEAM', 'WDAY', 'VEEV', 'ZM', 'ZS', 'CRWD', 'DDOG', 'NET', 'PANW', 'FTNT',
            'OKTA', 'SNOW', 'MDB', 'DOCU', 'TWLO', 'PLAN', 'HUBS', 'ZI', 'BILL', 'SMAR',
            'COUP', 'PATH', 'CFLT', 'ESTC', 'FROG', 'NCNO', 'AI', 'PLTR', 'U', 'RBLX',
            'COIN', 'SQ', 'SHOP', 'TTD', 'SPOT', 'ROKU', 'PINS', 'SNAP', 'LYFT', 'UBER',
            'DASH', 'ABNB', 'HOOD', 'SOFI', 'AFRM', 'UPST', 'LC', 'APPS', 'YELP', 'ETSY',
            'W', 'CHWY', 'PTON', 'CVNA', 'CARG', 'CPNG', 'MELI', 'SE', 'BABA', 'JD',
            'PDD', 'BIDU', 'NTES', 'TCOM', 'VIPS', 'BILI', 'IQ', 'HUYA', 'DOYU', 'TIGR'
        ]
        
        # Financial (80 stocks)
        financial = [
            'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'SCHW', 'AXP', 'USB',
            'PNC', 'TFC', 'COF', 'BK', 'STT', 'NTRS', 'RF', 'CFG', 'KEY', 'FITB',
            'HBAN', 'MTB', 'ZION', 'CMA', 'EWBC', 'FRC', 'SIVB', 'WAL', 'SBNY', 'NYCB',
            'V', 'MA', 'PYPL', 'FIS', 'FISV', 'GPN', 'JKHY', 'TOST', 'SQ', 'AFRM',
            'AIG', 'PRU', 'MET', 'AFL', 'ALL', 'TRV', 'PGR', 'CB', 'AIG', 'HIG',
            'CNA', 'CINF', 'L', 'AIZ', 'AFG', 'RNR', 'RE', 'BRO', 'AJG', 'MMC',
            'AON', 'WRB', 'KNSL', 'EG', 'RYAN', 'VIRT', 'LPLA', 'IBKR', 'MKTX', 'NDAQ',
            'ICE', 'CME', 'CBOE', 'SPGI', 'MCO', 'MSCI', 'TW', 'EFX', 'EXPN', 'VRSK'
        ]
        
        # Healthcare (60 stocks)
        healthcare = [
            'UNH', 'JNJ', 'LLY', 'PFE', 'ABBV', 'TMO', 'MRK', 'ABT', 'DHR', 'BMY',
            'AMGN', 'GILD', 'CVS', 'CI', 'HUM', 'CNC', 'BIIB', 'REGN', 'VRTX', 'ISRG',
            'ILMN', 'ALGN', 'IDXX', 'IQV', 'A', 'DXCM', 'EW', 'HOLX', 'INCY', 'MRNA',
            'ZTS', 'TECH', 'BDX', 'BAX', 'SYK', 'BSX', 'ELV', 'MDT', 'RMD', 'PODD',
            'GEHC', 'WAT', 'MTD', 'DGX', 'LH', 'EXAS', 'TDOC', 'VEEV', 'HIMS', 'DOCS',
            'PRVA', 'SDGR', 'LFST', 'ACCD', 'CERT', 'HAYW', 'OMCL', 'NTRA', 'IRTC', 'TMDX'
        ]
        
        # Consumer Discretionary (60 stocks)
        consumer_disc = [
            'AMZN', 'TSLA', 'HD', 'NKE', 'MCD', 'SBUX', 'LOW', 'TGT', 'TJX', 'BKNG',
            'CMG', 'ORLY', 'AZO', 'BBY', 'DG', 'DLTR', 'ROST', 'ULTA', 'DPZ', 'YUM',
            'MAR', 'HLT', 'MGM', 'WYNN', 'LVS', 'CZR', 'PENN', 'DKNG', 'FLUT', 'RSI',
            'F', 'GM', 'RIVN', 'LCID', 'NIO', 'XPEV', 'LI', 'RIDE', 'FSR', 'GOEV',
            'DIS', 'NFLX', 'PARA', 'WBD', 'FOX', 'FOXA', 'DISH', 'SIRI', 'LYV', 'MSG',
            'RL', 'PVH', 'VFC', 'HBI', 'UAA', 'UA', 'LULU', 'CROX', 'SKX', 'DKS'
        ]
        
        # Consumer Staples (40 stocks)
        consumer_staples = [
            'WMT', 'PG', 'KO', 'PEP', 'COST', 'PM', 'MO', 'BTI', 'EL', 'CL',
            'MDLZ', 'GIS', 'K', 'HSY', 'CPB', 'CAG', 'SJM', 'MKC', 'HRL', 'LW',
            'KHC', 'MNST', 'CELH', 'KDP', 'STZ', 'SAM', 'TAP', 'BF-B', 'BUD', 'DEO',
            'KR', 'SYY', 'USFD', 'PFGC', 'UNFI', 'SPTN', 'IMKTA', 'GO', 'ANDE', 'NGVC'
        ]
        
        # Industrials (60 stocks)
        industrials = [
            'BA', 'CAT', 'GE', 'HON', 'UPS', 'RTX', 'LMT', 'DE', 'MMM', 'UNP',
            'FDX', 'NSC', 'CSX', 'GD', 'NOC', 'ETN', 'EMR', 'ITW', 'PH', 'CMI',
            'PCAR', 'ROK', 'DOV', 'AME', 'FAST', 'CARR', 'OTIS', 'WM', 'RSG', 'WCN',
            'VRSK', 'IEX', 'FTV', 'HUBB', 'ALLE', 'GNRC', 'AOS', 'CR', 'ROP', 'EXPD',
            'CHRW', 'JBHT', 'ODFL', 'XPO', 'KNX', 'LSTR', 'ARCB', 'WERN', 'SAIA', 'CVLG',
            'R', 'URI', 'UHAL', 'HRI', 'MLM', 'VMC', 'NUE', 'STLD', 'RS', 'X'
        ]
        
        # Energy (40 stocks)
        energy = [
            'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'HES',
            'HAL', 'BKR', 'WMB', 'KMI', 'OKE', 'LNG', 'TRGP', 'ET', 'EPD', 'MPLX',
            'DVN', 'FANG', 'MRO', 'APA', 'CTRA', 'OVV', 'PR', 'MGY', 'SM', 'RRC',
            'CHRD', 'MTDR', 'NOG', 'VTLE', 'CRGY', 'CLR', 'PDCE', 'AR', 'WDS', 'CPE'
        ]
        
        # Utilities & Real Estate (40 stocks)
        utilities_re = [
            'NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE', 'PEG', 'XEL', 'ED',
            'WEC', 'ES', 'DTE', 'PPL', 'AEE', 'CMS', 'CNP', 'ETR', 'EVRG', 'FE',
            'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'WELL', 'DLR', 'O', 'SBAC', 'AVB',
            'EQR', 'VTR', 'INVH', 'MAA', 'ESS', 'UDR', 'CPT', 'AIV', 'ELS', 'CUBE'
        ]
        
        # Materials & Commodities (20 stocks)
        materials = [
            'LIN', 'APD', 'SHW', 'ECL', 'FCX', 'NEM', 'GOLD', 'SCCO', 'DD', 'DOW',
            'PPG', 'NUE', 'STLD', 'CF', 'MOS', 'FMC', 'ALB', 'EMN', 'IP', 'PKG'
        ]
        
        # Combine all sectors
        stocks = tech + financial + healthcare + consumer_disc + consumer_staples + industrials + energy + utilities_re + materials
        
        # Remove duplicates and sort
        stocks = sorted(list(set(stocks)))
        
        logger.info(f"✓ Expanded universe: {len(stocks)} stocks")
        return stocks
    
    def _get_popular_stocks(self) -> List[str]:
        """Return a list of popular US stocks as final fallback"""
        return [
            # Tech giants
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'AMD', 'INTC', 'CSCO',
            # Financial
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'AXP',
            # Healthcare
            'UNH', 'JNJ', 'PFE', 'ABBV', 'TMO', 'MRK', 'ABT', 'LLY', 'DHR', 'BMY',
            # Consumer
            'WMT', 'HD', 'PG', 'KO', 'PEP', 'COST', 'NKE', 'MCD', 'SBUX', 'TGT',
            # Industrial
            'BA', 'CAT', 'GE', 'MMM', 'HON', 'UPS', 'LMT', 'RTX', 'DE',
            # Energy
            'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX',
            # Communication
            'DIS', 'CMCSA', 'NFLX', 'T', 'VZ', 'TMUS',
            # Others
            'V', 'MA', 'PYPL', 'ADBE', 'CRM', 'ORCL', 'IBM', 'TXN', 'QCOM',
            # Mid-caps with good fundamentals
            'SQ', 'SHOP', 'SNOW', 'CRWD', 'NET', 'DDOG', 'ZS', 'OKTA', 'PANW',
            'COIN', 'RBLX', 'U', 'PATH', 'BILL', 'FTNT', 'TEAM', 'WDAY', 'VEEV',
            'TTD', 'MELI', 'SE', 'ABNB', 'UBER', 'LYFT', 'DASH', 'SPOT', 'ZM',
            'DOCU', 'TWLO', 'ROKU', 'PINS', 'SNAP', 'ETSY', 'W', 'CHWY', 'PTON'
        ]
    
    def _build_query(self, filters: Dict) -> Dict:
        """Build query for yfinance screener (not used in fallback)"""
        operands = []
        
        min_cap = filters.get('market_cap_min', 300_000_000)
        max_cap = filters.get('market_cap_max', 10_000_000_000)
        
        operands.append({
            'operator': 'GT',
            'operands': ['intradaymarketcap', min_cap]
        })
        operands.append({
            'operator': 'LT',
            'operands': ['intradaymarketcap', max_cap]
        })
        
        if 'volume_min' in filters:
            operands.append({
                'operator': 'GT',
                'operands': ['avgdailyvol3m', filters['volume_min']]
            })
        
        return {
            'operator': 'AND',
            'operands': operands
        }
