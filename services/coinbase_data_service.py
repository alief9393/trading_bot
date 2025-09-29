import ccxt
import pandas as pd
from datetime import datetime
import time

class CoinbaseDataService:
    def __init__(self):
        try:
            self.exchange = ccxt.coinbaseadvanced()
            self.exchange.load_markets()
            print("CoinbaseDataService: CCXT exchange interface for Coinbase initialized successfully.")
        except Exception as e:
            print(f"CoinbaseDataService: Error initializing exchange: {e}")
            self.exchange = None

    def get_all_historical_data(self, symbol: str, timeframe: str, start_date: str) -> pd.DataFrame | None:
        if not self.exchange:
            print("CoinbaseDataService: Exchange is not initialized.")
            return None

        fetch_timeframe = '1h' if timeframe == '4h' else timeframe
        ccxt_symbol = symbol.replace('/', '-')

        print(f"CoinbaseDataService: Fetching all historical klines for {ccxt_symbol} on {fetch_timeframe} since {start_date}...")
        try:
            since = self.exchange.parse8601(f"{start_date} 00:00:00Z")
            all_ohlcv = []

            while True:
                print(f"Fetching chunk starting from {self.exchange.iso8601(since)}...")
                ohlcv_chunk = self.exchange.fetch_ohlcv(ccxt_symbol, fetch_timeframe, since, limit=300)
                
                if not ohlcv_chunk:
                    break
                
                all_ohlcv.extend(ohlcv_chunk)
                
                since = ohlcv_chunk[-1][0] + 1
                
                time.sleep(self.exchange.rateLimit / 1000)

            if not all_ohlcv:
                print(f"CoinbaseDataService: No data returned for {ccxt_symbol}.")
                return None

            df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df[~df.index.duplicated(keep='first')] 
            
            if timeframe == '4h':
                print("CoinbaseDataService: Resampling 1H data to 4H...")
                agg_dict = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}
                df = df.resample('4H', origin='start_day').agg(agg_dict).dropna()

            print(f"CoinbaseDataService: Downloaded and processed {len(df)} total {timeframe} candles.")
            return df
            
        except Exception as e:
            print(f"CoinbaseDataService: A general error occurred while fetching data: {e}")
            return None