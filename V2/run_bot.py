import pandas as pd
import numpy as np
import ccxt
import pandas_ta as ta
from scipy.signal import find_peaks
import os
import time
import requests
import configparser
import datetime

def send_telegram_notification(message):
    print("   Attempting to send Telegram notification...")
    try:
        config = configparser.ConfigParser()
        config.read('config.ini')
        bot_token = config['telegram']['bot_token']
        channel_id = config['telegram']['channel_id']
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {'chat_id': channel_id, 'text': message, 'parse_mode': 'Markdown'}
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("   Telegram notification sent successfully!")
        else:
            print(f"   Failed to send Telegram notification. Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"   An error occurred while sending Telegram notification: {e}")

def run_bot_cycle():
    print(f"\n===== CYCLE START: {pd.Timestamp.now(tz='UTC').strftime('%Y-%m-%d %H:%M:%S UTC')} =====")
    try:
        print("   Fetching latest data from exchange...")
        exchange = ccxt.coinbaseadvanced()
        exchange.proxies = {'http': None, 'https': None}
        symbol_input = 'BTC/USD'; ccxt_symbol = symbol_input.replace('/', '-')

        ohlcv_h1 = exchange.fetch_ohlcv(ccxt_symbol, '1h', limit=1008)
        df_h1 = pd.DataFrame(ohlcv_h1, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']); df_h1['timestamp'] = pd.to_datetime(df_h1['timestamp'], unit='ms'); df_h1.set_index('timestamp', inplace=True)
        agg_dict = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}
        df_h4 = df_h1.resample('4H', origin='start_day').agg(agg_dict).dropna()

        ohlcv_m15 = exchange.fetch_ohlcv(ccxt_symbol, '15m', limit=1000)
        df_m15 = pd.DataFrame(ohlcv_m15, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']); df_m15['timestamp'] = pd.to_datetime(df_m15['timestamp'], unit='ms')
        
        print("   Data fetch complete.")

        print("   Calculating indicators...")
        df_h4['EMA_55'] = ta.ema(df_h4['close'], length=55)
        df_h4['EMA_200'] = ta.ema(df_h4['close'], length=200)
    
        df_h1['RSI_14'] = ta.rsi(df_h1['close'], length=14); df_h1['ATR_14'] = ta.atr(df_h1['high'], df_h1['low'], df_h1['close'], length=14)
        peak_indices, _ = find_peaks(df_h1['high'], distance=5, prominence=df_h1['ATR_14'].mean()); trough_indices, _ = find_peaks(-df_h1['low'], distance=5, prominence=df_h1['ATR_14'].mean())
        df_h1['swing_high'] = np.nan; df_h1.loc[df_h1.index[peak_indices], 'swing_high'] = df_h1['high'].iloc[peak_indices]
        df_h1['swing_low'] = np.nan; df_h1.loc[df_h1.index[trough_indices], 'swing_low'] = df_h1['low'].iloc[trough_indices]
    
        df_m15['EMA_9'] = ta.ema(df_m15['close'], length=9)
        df_m15['EMA_21'] = ta.ema(df_m15['close'], length=21)
        df_m15['RSI_14'] = ta.rsi(df_m15['close'], length=14)
        df_m15['ATR_14'] = ta.atr(df_m15['high'], df_m15['low'], df_m15['close'], length=14)
        df_m15.ta.macd(append=True)
        
        df_h4.dropna(inplace=True); df_h1.dropna(inplace=True, subset=['RSI_14']); df_m15.dropna(inplace=True)
        print("   Indicators calculated successfully.")

        print("   Checking for the latest signal...")
        latest_m15 = df_m15.iloc[-2]; previous_m15 = df_m15.iloc[-3]
        current_time = latest_m15['timestamp']
        
        current_price = df_m15.iloc[-1]['close']
        print(f"   Current BTC Price: ${current_price:,.2f}")

        h4_check = df_h4[df_h4.index < current_time]
        if h4_check.empty: raise ValueError("Not enough H4 data for trend check.")

        # --- Logika Sinyal Pullback ---
        pullback_found = False
        is_uptrend = h4_check['close'].iloc[-1] > h4_check['EMA_55'].iloc[-1]
        h1_check = df_h1[df_h1.index < current_time]
        if not h1_check.empty:
            if is_uptrend:
                last_highs = h1_check[h1_check['swing_high'].notna()]; last_lows = h1_check[h1_check['swing_low'].notna()]
                if not last_highs.empty and not last_lows.empty:
                    last_high_idx = last_highs.index[-1]; relevant_lows = last_lows[last_lows.index < last_high_idx]
                    if not relevant_lows.empty:
                        last_low_idx = relevant_lows.index[-1]
                        sh, sl = h1_check['swing_high'].loc[last_high_idx], h1_check['swing_low'].loc[last_low_idx]
                        if sh > sl:
                            f_0618 = sh - (sh - sl) * 0.618
                            if h1_check['close'].iloc[-1] <= f_0618 and h1_check['RSI_14'].iloc[-1] < 45:
                                ema_cross_up = latest_m15['close'] > latest_m15['EMA_21'] and previous_m15['close'] <= previous_m15['EMA_21']
                                macd_state_bullish = latest_m15['MACD_12_26_9'] > latest_m15['MACDs_12_26_9']
                                if ema_cross_up and macd_state_bullish:
                                    entry_price = latest_m15['close']; current_atr = latest_m15['ATR_14']
                                    stop_loss = entry_price - (2.0 * current_atr); take_profit = entry_price + (4.0 * current_atr)
                                    message = (f"PULLBACK BUY BTC/USD\n\nEntry: ${entry_price:,.2f}\nSL: ${stop_loss:,.2f}\nTP: ${take_profit:,.2f}")
                                    send_telegram_notification(message)
                                    pullback_found = True
            else:
                last_highs = h1_check[h1_check['swing_high'].notna()]; last_lows = h1_check[h1_check['swing_low'].notna()]
                if not last_highs.empty and not last_lows.empty:
                    last_low_idx = last_lows.index[-1]; relevant_highs = last_highs[last_highs.index < last_low_idx]
                    if not relevant_highs.empty:
                        last_high_idx = relevant_highs.index[-1]
                        sh, sl = h1_check['swing_high'].loc[last_high_idx], h1_check['swing_low'].loc[last_low_idx]
                        if sh > sl:
                            f_0618 = sl + (sh - sl) * 0.618
                            if h1_check['close'].iloc[-1] >= f_0618 and h1_check['RSI_14'].iloc[-1] > 55:
                                ema_cross_down = latest_m15['close'] < latest_m15['EMA_21'] and previous_m15['close'] >= previous_m15['EMA_21']
                                macd_state_bearish = latest_m15['MACD_12_26_9'] < latest_m15['MACDs_12_26_9']
                                if ema_cross_down and macd_state_bearish:
                                    entry_price = latest_m15['close']; current_atr = latest_m15['ATR_14']
                                    stop_loss = entry_price + (2.0 * current_atr); take_profit = entry_price - (4.0 * current_atr)
                                    message = (f"PULLBACK SELL BTC/USD\n\nEntry: ${entry_price:,.2f}\nSL: ${stop_loss:,.2f}\nTP: ${take_profit:,.2f}")
                                    send_telegram_notification(message)
                                    pullback_found = True
        
        # --- Logika Sinyal Momentum ---
        if not pullback_found:
            strong_uptrend = h4_check['close'].iloc[-1] > h4_check['EMA_55'].iloc[-1] and h4_check['EMA_55'].iloc[-1] > h4_check['EMA_200'].iloc[-1]
            momentum_buy_trigger = latest_m15['EMA_9'] > latest_m15['EMA_21'] and previous_m15['EMA_9'] <= previous_m15['EMA_21']
            rsi_momentum_confirm = latest_m15['RSI_14'] > 60
            
            if strong_uptrend and momentum_buy_trigger and rsi_momentum_confirm:
                entry_price = latest_m15['close']; current_atr = latest_m15['ATR_14']
                stop_loss = entry_price - (2.0 * current_atr); take_profit = entry_price + (4.0 * current_atr)
                message = (f"MOMENTUM BUY BTC/USD\n\nEntry: ${entry_price:,.2f}\nSL: ${stop_loss:,.2f}\nTP: ${take_profit:,.2f}")
                send_telegram_notification(message)

            strong_downtrend = h4_check['close'].iloc[-1] < h4_check['EMA_55'].iloc[-1] and h4_check['EMA_55'].iloc[-1] < h4_check['EMA_200'].iloc[-1]
            momentum_sell_trigger = latest_m15['EMA_9'] < latest_m15['EMA_21'] and previous_m15['EMA_9'] >= previous_m15['EMA_21']
            rsi_momentum_confirm_sell = latest_m15['RSI_14'] < 40

            if strong_downtrend and momentum_sell_trigger and rsi_momentum_confirm_sell:
                entry_price = latest_m15['close']; current_atr = latest_m15['ATR_14']
                stop_loss = entry_price + (2.0 * current_atr); take_profit = entry_price - (4.0 * current_atr)
                message = (f"MOMENTUM SELL BTC/USD\n\nEntry: ${entry_price:,.2f}\nSL: ${stop_loss:,.2f}\nTP: ${take_profit:,.2f}")
                send_telegram_notification(message)

    except Exception as e:
        print(f"   An error occurred during the cycle: {e}")

if __name__ == '__main__':
    while True:
        try:
            run_bot_cycle()
            now = datetime.datetime.now(datetime.timezone.utc)
            next_run_minute = (now.minute // 15 + 1) * 15
            
            if next_run_minute >= 60:
                next_run_time = now.replace(minute=0, second=1, microsecond=0) + datetime.timedelta(hours=1)
            else:
                next_run_time = now.replace(minute=next_run_minute, second=1, microsecond=0)

            if next_run_time <= now:
                 next_run_time += datetime.timedelta(minutes=15)

            sleep_duration = (next_run_time - now).total_seconds()
            
            if sleep_duration > 0:
                print(f"===== CYCLE END. Sleeping for {sleep_duration:.2f} seconds until {next_run_time.strftime('%H:%M:%S')} UTC =====")
                time.sleep(sleep_duration)

        except KeyboardInterrupt:
            print("\nBot stopped by user.")
            break
        except Exception as e:
            print(f"FATAL ERROR in main loop: {e}")
            print("Restarting cycle in 1 minute...")
            time.sleep(60)