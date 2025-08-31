# main_scheduler.py (FINAL Multi-Asset H4 Version)

import configparser
import json
from datetime import datetime
import time
import pytz

# Import all services
from services.data_service import DataService
from services.indicator_service import IndicatorService
from services.ml_service import MLService
from services.heuristic_service import HeuristicService
from services.telegram_service import TelegramService
from services.trade_logger import TradeLogger
from services.trade_manager import TradeManagerService

def run_trade_cycle_for_symbol(config, symbol: str):
    """
    Runs the complete H4 Swing signal generation pipeline for a single symbol.
    """
    strategy_name = f"H4 Swing ({symbol})"
    print(f"\n[{datetime.now()}] --- Running {strategy_name} Cycle ---")
    
    # Create filenames specific to this symbol
    safe_symbol_name = symbol.replace('/', '_').lower()
    status_file = f"{safe_symbol_name}_status.json"
    log_file = f"{safe_symbol_name}_log.csv"
    model_file = f"models/{safe_symbol_name}_h4.pkl"

    # Initialize services needed for signal generation
    data_svc = DataService(api_key=config['exchange']['api_key'], api_secret=config['exchange']['api_secret'])
    telegram_svc = TelegramService(bot_token=config['telegram']['bot_token'], channel_id=config['telegram']['channel_id'])
    
    # Read status to see if we can hunt for a new trade
    try:
        with open(status_file, 'r') as f:
            status = json.load(f)
    except FileNotFoundError:
        # If the file doesn't exist, create it.
        with open(status_file, 'w') as f:
            json.dump({"is_trade_open": False, "current_trade": {}}, f, indent=2)
        status = {"is_trade_open": False}

    if status.get('is_trade_open', False):
        print(f"{strategy_name}: A trade is already open. Skipping new signal analysis.")
        return

    # Hunt for a new trade
    print(f"{strategy_name}: No open trade. Proceeding with analysis.")
    indicator_svc = IndicatorService()
    ml_svc = MLService(model_path=model_file)
    heuristic_svc = HeuristicService()
    trade_logger = TradeLogger(log_file)
    
    market_df = data_svc.get_market_data(symbol=symbol, timeframe='4h')
    analysis_df = indicator_svc.add_all_indicators(market_df)
    prediction = ml_svc.get_prediction(analysis_df)
    result = heuristic_svc.generate_trade_signal(prediction, analysis_df)

    if result['status'] == 'success':
        trade_signal = result['signal']
        telegram_svc.send_signal(trade_signal, symbol)
        trade_logger.log_new_signal(symbol, trade_signal)
        with open(status_file, 'w') as f:
            json.dump({"is_trade_open": True, "current_trade": trade_signal}, f, indent=2)
    else:
        print(f"{strategy_name}: No valid signal found. Reason: {result['status']}")
        telegram_svc.send_market_update(result['status'], result.get('reason'))

# --- The Main Execution Block ---
if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')

    if 'YOUR_TELEGRAM_BOT_TOKEN_HERE' in config['telegram']['bot_token']:
        print("FATAL ERROR: Please set your Telegram bot token in config.ini before running.")
        exit()

    # Get the list of symbols from the config file
    symbols_to_trade = [symbol.strip() for symbol in config['parameters']['symbols'].split(',')]
    
    # Initialize Core Services that are always needed
    data_svc = DataService(api_key=config['exchange']['api_key'], api_secret=config['exchange']['api_secret'])
    telegram_svc = TelegramService(bot_token=config['telegram']['bot_token'], channel_id=config['telegram']['channel_id'])

    # Create a list of Trade Managers, one for each symbol
    trade_managers = [
        TradeManagerService(data_svc, telegram_svc, f"{s.replace('/', '_').lower()}_log.csv", f"{s.replace('/', '_').lower()}_status.json", s)
        for s in symbols_to_trade
    ]
    
    print(f"--- High-Frequency, Multi-Asset Bot Started for: {symbols_to_trade} ---")
    print("Trade management will run every minute.")
    print("Signal generation will run on H4 candle closes.")
    print("Press Ctrl+C to exit.")

    last_h4_run_hour = -1

    try:
        while True:
            now_utc = datetime.now(pytz.utc)
            current_hour = now_utc.hour
            current_minute = now_utc.minute
            
            # --- 1. HIGH-FREQUENCY TRADE MANAGEMENT (Runs every minute) ---
            print(f"[{now_utc.strftime('%Y-%m-%d %H:%M:%S')}] Checking open trades for all symbols...")
            for manager in trade_managers:
                manager.check_open_trade()
            
            # --- 2. SIGNAL GENERATION (Runs only at H4 candle close times) ---
            if current_hour % 4 == 0 and current_minute >= 1 and last_h4_run_hour != current_hour:
                for symbol in symbols_to_trade:
                    run_trade_cycle_for_symbol(config, symbol)
                last_h4_run_hour = current_hour

            # Wait for 1 minute before the next loop
            time.sleep(60)

    except (KeyboardInterrupt, SystemExit):
        print("\nBot stopped.")