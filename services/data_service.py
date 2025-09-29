import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time

class DataService:
    def __init__(self):
        try:
            self.exchange = ccxt.coinbaseadvanced()
            self.exchange.load_markets()
            print("DataService: Unified CCXT interface for Coinbase initialized successfully.")
        except Exception as e:
            print(f"DataService: Error initializing exchange: {e}")
            self.exchange = None

    def get_market_data(self, symbol: str, timeframe: str, limit: int = 500, is_startup_run: bool = False) -> pd.DataFrame | None:
        """
        Fetches a recent chunk of market data for LIVE analysis.
        """
        if not self.exchange: return None

        try:
            ccxt_symbol = symbol.replace('/', '-')
            
            if timeframe == '4h':
                print(f"DataService (Live): '4h' requested. Fetching a robust chunk of 1h data...")
                current_timestamp_ms = int(time.time() * 1000)
                since = current_timestamp_ms - (1000 * 60 * 60 * 1000)
                all_ohlcv = []
                
                while True:
                    print(f"DataService (Live): Fetching 1h chunk since {self.exchange.iso8601(since)}...")
                    ohlcv_chunk = self.exchange.fetch_ohlcv(ccxt_symbol, '1h', since, limit=300)
                    if not ohlcv_chunk:
                        break
                    
                    all_ohlcv.extend(ohlcv_chunk)
                    since = ohlcv_chunk[-1][0] + 1
                    
                    if since > self.exchange.milliseconds():
                        break
                    time.sleep(self.exchange.rateLimit / 1000)
                
                if not all_ohlcv:
                    print("DataService (Live): Failed to fetch any 1h data for resampling.")
                    return None
                
                df_1h = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df_1h['timestamp'] = pd.to_datetime(df_1h['timestamp'], unit='ms')
                df_1h.set_index('timestamp', inplace=True)
                
                print(f"DataService (Live): Fetched {len(df_1h)} total 1h candles. Resampling to 4H...")
                agg_dict = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}
                df = df_1h.resample('4H', origin='start_day').agg(agg_dict)
                
            else: # For other timeframes (like the 1m trade manager), fetch directly.
                ohlcv = self.exchange.fetch_ohlcv(ccxt_symbol, timeframe, limit=limit)
                if not ohlcv: return None
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
            
            if not is_startup_run:
                df = df.iloc[:-1]
                print("DataService (Live): Scheduled run. Removed final (incomplete) candle.")
            
            df.dropna(inplace=True)
            print(f"DataService (Live): Successfully processed {len(df)} candles.")
            return df

        except Exception as e:
            print(f"DataService (get_market_data): An error occurred: {e}")
            return None

    def get_all_historical_data(self, symbol: str, timeframe: str, start_date: str) -> pd.DataFrame | None:
        if not self.exchange: return None

        fetch_timeframe = '1h' if timeframe == '4h' else timeframe
        ccxt_symbol = symbol.replace('/', '-')

        print(f"DataService (Hist): Fetching all klines for {ccxt_symbol} on {fetch_timeframe} since {start_date}...")
        try:
            since = self.exchange.parse8601(f"{start_date} 00:00:00Z")
            all_ohlcv = []
            
            while True:
                ohlcv_chunk = self.exchange.fetch_ohlcv(ccxt_symbol, fetch_timeframe, since, limit=300)
                if not ohlcv_chunk: break
                all_ohlcv.extend(ohlcv_chunk)
                since = ohlcv_chunk[-1][0] + 1
                time.sleep(self.exchange.rateLimit / 1000)

            if not all_ohlcv: return None

            df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df[~df.index.duplicated(keep='first')]

            if timeframe == '4h':
                print("DataService (Hist): Resampling 1H data to 4H...")
                agg_dict = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}
                df = df.resample('4H', origin='start_day').agg(agg_dict).dropna()

            print(f"DataService (Hist): Downloaded and processed {len(df)} total {timeframe} candles.")
            return df
            
        except Exception as e:
            print(f"DataService (get_all_historical_data): An error occurred: {e}")
            return None