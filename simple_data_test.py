# simple_data_test.py

import ccxt
from datetime import datetime

print("--- Starting Simple CCXT Coinbase Data Test ---")

# 1. Initialize the exchange
try:
    exchange = ccxt.coinbaseadvanced()
    exchange.load_markets()
    print("SUCCESS: Exchange initialized successfully.")
except Exception as e:
    print(f"FATAL: Could not initialize exchange. Error: {e}")
    exit() # Exit the script if connection fails

# 2. Define our request parameters
symbol = 'BTC/USD'
timeframe = '1h' # We will request 1h data directly, just like our service does
limit = 10       # Let's just ask for the 10 most recent candles

print(f"\nAttempting to fetch the last {limit} '{timeframe}' candles for '{symbol}'...")

# 3. Make the API call
try:
    # This is the raw API call. We will inspect its direct output.
    raw_ohlcv_data = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

    # 4. Analyze the raw response
    print("\n--- RAW DATA ANALYSIS ---")
    if raw_ohlcv_data is None:
        print("RESULT: API returned None.")
    elif not raw_ohlcv_data:
        print("RESULT: API returned an EMPTY list [].")
    else:
        print(f"SUCCESS: API returned a list with {len(raw_ohlcv_data)} candles.")
        print("Here is the raw data for the most recent candle:")
        
        # The data is a list of lists: [timestamp, open, high, low, close, volume]
        most_recent_candle = raw_ohlcv_data[-1]
        
        # Convert timestamp to a human-readable format
        timestamp_ms = most_recent_candle[0]
        human_readable_time = datetime.utcfromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        print(f"  - Timestamp: {most_recent_candle[0]} ({human_readable_time})")
        print(f"  - Open:      {most_recent_candle[1]}")
        print(f"  - High:      {most_recent_candle[2]}")
        print(f"  - Low:       {most_recent_candle[3]}")
        print(f"  - Close:     {most_recent_candle[4]}")
        print(f"  - Volume:    {most_recent_candle[5]}")

except Exception as e:
    print(f"\nERROR: An error occurred during the fetch_ohlcv call: {e}")

print("\n--- Test Complete ---")