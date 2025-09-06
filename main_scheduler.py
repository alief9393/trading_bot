# main_scheduler.py (The FINAL MTF "General and Scout" Version)

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

def run_h4_bias_check(config, symbol: str, data_svc, telegram_svc, is_startup_run: bool = False):
    """ The "General": Runs every 4 hours to establish a new strategic bias. """
    strategy_name = f"H4 Bias Hunter ({symbol})"
    print(f"\n[{datetime.now()}] --- Running {strategy_name} ---")
    
    status_file = f"{symbol.replace('/', '_').lower()}_status.json"
    model_file = f"models/{symbol.replace('/', '_').lower()}_h4.pkl"

    # Initialize services for this task
    indicator_svc = IndicatorService()
    ml_svc = MLService(model_path=model_file)
    heuristic_svc = HeuristicService()
    
    market_df_h4 = data_svc.get_market_data(symbol=symbol, timeframe='4h', is_startup_run=is_startup_run)
    if market_df_h4 is None or market_df_h4.empty: return

    analysis_df_h4 = indicator_svc.add_all_indicators(market_df_h4)
    if analysis_df_h4 is None or analysis_df_h4.empty: return

    prediction = ml_svc.get_prediction(analysis_df_h4)
    result = heuristic_svc.generate_h4_bias(prediction, analysis_df_h4)

    if result['status'] == 'success':
        bias_details = result['bias_details']
        print(f"{strategy_name}: Found a new {bias_details['bias']} bias. Updating state to WATCHING.")
        
        # Update the state file to reflect the new hunt
        new_status = {"state": "WATCHING_FOR_ENTRY", "bias_details": bias_details}
        with open(status_file, 'w') as f:
            json.dump(new_status, f, indent=2)
        
        telegram_svc.send_bias_alert(bias_details, symbol)

def run_h1_entry_hunt(config, symbol: str, data_svc, telegram_svc, heuristic_svc):
    """ The "Scout": Runs every hour to check for a precise entry confirmation. """
    strategy_name = f"H1 Entry Scout ({symbol})"
    print(f"\n[{datetime.now()}] --- Running {strategy_name} ---")

    status_file = f"{symbol.replace('/', '_').lower()}_status.json"
    log_file = f"{symbol.replace('/', '_').lower()}_log.csv"
    
    market_df_h1 = data_svc.get_market_data(symbol=symbol, timeframe='1h', limit=5) # Get a few recent H1 candles
    if market_df_h1 is None or market_df_h1.empty: return
    
    with open(status_file, 'r') as f:
        status = json.load(f)
    
    bias_details = status['bias_details']
    
    # Check if price is near the pullback level before looking for confirmation
    if abs(market_df_h1.iloc[-1]['close'] - bias_details['pullback_level']) < (bias_details['sl'] - bias_details['pullback_level']):
        if heuristic_svc.confirm_h1_entry(market_df_h1, bias_details['bias']):
            print(f"{strategy_name}: H1 entry CONFIRMED. Executing trade.")
            
            # Use the live close price for the final entry
            final_trade_details = bias_details.copy()
            final_trade_details['entry'] = market_df_h1.iloc[-1]['close']

            telegram_svc.send_execution_alert(final_trade_details, symbol)
            trade_logger = TradeLogger(log_file)
            trade_logger.log_new_signal(symbol, final_trade_details)
            
            # Update state to IN_TRADE
            new_status = {"state": "IN_TRADE", "trade_details": final_trade_details}
            with open(status_file, 'w') as f:
                json.dump(new_status, f, indent=2)

# In main_scheduler.py -- The FINAL main execution block

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')

    if 'YOUR_TELEGRAM_BOT_TOKEN_HERE' in config['telegram']['bot_token']:
        print("FATAL ERROR: Please set your Telegram bot token in config.ini before running.")
        exit()

    symbols_to_trade = [symbol.strip() for symbol in config['parameters']['symbols'].split(',')]
    
    # Initialize services that are used in the main loop
    data_svc = DataService()
    telegram_svc = TelegramService(bot_token=config['telegram']['bot_token'], channel_id=config['telegram']['channel_id'])
    heuristic_svc = HeuristicService() # The Scout
    
    trade_managers = [TradeManagerService(data_svc, telegram_svc, f"{s.replace('/', '_').lower()}_log.csv", f"{s.replace('/', '_').lower()}_status.json", s) for s in symbols_to_trade]
    
    # --- IMMEDIATE FIRST RUN ON STARTUP ---
    print("\n" + "="*50)
    print("--- Running the first manual BIAS CHECK for all strategies on startup ---")
    print("="*50)
    
    for symbol in symbols_to_trade:
        # We will re-use the H4 bias check function, but tell it this is a startup run
        # Note: This requires a small modification to run_h4_bias_check
        run_h4_bias_check(config, symbol, data_svc, telegram_svc, is_startup_run=True)

    print("\n" + "="*50)
    print("--- First manual cycle finished. Starting continuous patrol. ---")
    print("="*50)

    last_h4_run_hour = -1
    last_h1_run_hour = -1

    try:
        while True:
            now_utc = datetime.now(pytz.utc)
            
            # 1. HIGH-FREQUENCY MANAGEMENT (Every minute)
            print(f"[{now_utc.strftime('%H:%M:%S')}] Running management cycle...")
            for manager in trade_managers:
                manager.check_open_trade()
            
            # 2. LOW-FREQUENCY STRATEGY (H4 Bias on Schedule)
            if now_utc.hour % 4 == 0 and now_utc.minute >= 1 and last_h4_run_hour != now_utc.hour:
                for symbol in symbols_to_trade:
                    with open(f"{symbol.replace('/', '_').lower()}_status.json", 'r') as f:
                        status = json.load(f)
                    if status.get('state') == "HUNTING":
                        # Scheduled runs are NOT startup runs
                        run_h4_bias_check(config, symbol, data_svc, telegram_svc, is_startup_run=False)
                last_h4_run_hour = now_utc.hour

            # 3. MEDIUM-FREQUENCY TACTICS (H1 Entry Hunt)
            if now_utc.minute >= 1 and last_h1_run_hour != now_utc.hour:
                for symbol in symbols_to_trade:
                    try:
                        with open(f"{symbol.replace('/', '_').lower()}_status.json", 'r') as f:
                            status = json.load(f)
                        if status.get('state') == "WATCHING_FOR_ENTRY":
                            run_h1_entry_hunt(config, symbol, data_svc, telegram_svc, heuristic_svc)
                    except FileNotFoundError:
                        continue # Ignore if status file doesn't exist yet
                last_h1_run_hour = now_utc.hour

            time.sleep(60)

    except (KeyboardInterrupt, SystemExit):
        print("\nBot stopped.")