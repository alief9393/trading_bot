# services/data_service.py
import pandas as pd
from binance.client import Client

class DataService:
    """
    Service responsible for fetching market data using the 'python-binance' library.
    This version is configured for Binance.US and works with "Read-Only" API keys.
    """
    def __init__(self, api_key: str, api_secret: str):
        """
        Initializes the service with API credentials.
        """
        try:
            # We use tld='us' to connect to the Binance.US platform
            self.client = Client(api_key, api_secret, tld='us') 
            # Ping the server to check the connection
            self.client.ping()
            print("DataService: Binance.US client initialized and connection successful (Read-Only).")
        except Exception as e:
            print(f"DataService: Error initializing Binance.US client: {e}")
            self.client = None

    def get_market_data(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame | None:
        """
        Fetches historical OHLCV data for a given symbol and timeframe.
        """
        if not self.client:
            print("DataService: Client is not initialized.")
            return None

        formatted_symbol = symbol.replace('/', '')

        # The library also has specific constants for timeframes. We need a mapping.
        timeframe_map = {
            '15m': Client.KLINE_INTERVAL_15MINUTE,
            '1h': Client.KLINE_INTERVAL_1HOUR,
            '4h': Client.KLINE_INTERVAL_4HOUR,
            '1d': Client.KLINE_INTERVAL_1DAY,
        }
        if timeframe not in timeframe_map:
            print(f"DataService: Unsupported timeframe '{timeframe}'.")
            return None
        
        binance_timeframe = timeframe_map[timeframe]

        print(f"DataService: Fetching {limit} klines for {formatted_symbol} on timeframe {timeframe}...")
        try:
            klines = self.client.get_klines(symbol=formatted_symbol, interval=binance_timeframe, limit=limit)
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])

            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df[['open', 'high', 'low', 'close', 'volume']]
            for col in df.columns:
                df[col] = pd.to_numeric(df[col])

            print("DataService: Data fetched and formatted successfully.")
            return df
        except Exception as e:
            print(f"DataService: An error occurred while fetching data: {e}")
            return None
    
    def get_all_historical_data(self, symbol: str, timeframe: str, start_date: str) -> pd.DataFrame | None:
        """
        Fetches the maximum available historical data from a given start date using a generator.
        """
        if not self.client:
            print("DataService: Client is not initialized.")
            return None

        formatted_symbol = symbol.replace('/', '')
        timeframe_map = {
            '15m': Client.KLINE_INTERVAL_15MINUTE,
            '1h': Client.KLINE_INTERVAL_1HOUR,
            '4h': Client.KLINE_INTERVAL_4HOUR,
            '1d': Client.KLINE_INTERVAL_1DAY,
        }
        if timeframe not in timeframe_map:
            print(f"DataService: Unsupported timeframe '{timeframe}'.")
            return None
        
        binance_timeframe = timeframe_map[timeframe]

        print(f"DataService: Fetching all historical klines for {formatted_symbol} since {start_date}...")
        try:
            klines_generator = self.client.get_historical_klines_generator(
                formatted_symbol, binance_timeframe, start_date
            )
            klines = list(klines_generator)
            
            print(f"DataService: Downloaded {len(klines)} total klines.")

            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])

            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df[['open', 'high', 'low', 'close', 'volume']]
            for col in df.columns:
                df[col] = pd.to_numeric(df[col])

            print("DataService: All historical data fetched and formatted successfully.")
            return df
        except Exception as e:
            print(f"DataService: An error occurred while fetching all historical data: {e}")
            return None