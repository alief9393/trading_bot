import configparser
import json
from datetime import datetime
import time
import pytz

from apscheduler.schedulers.blocking import BlockingScheduler

from services.data_service import DataService
from services.indicator_service import IndicatorService
from services.ml_service import MLService
from services.heuristic_service import HeuristicService
from services.telegram_service import TelegramService
from services.trade_logger import TradeLogger
from services.trade_manager import TradeManagerService

def run_trade_cycle_for_symbol(config, symbol: str):
    strategy_name = f"H4 Swing ({symbol})"
    print(f"\n[{datetime.now()}] --- Running {strategy_name} Cycle ---")
    
    safe_symbol_name = symbol.replace('/', '_').lower()
    status_file = f"{safe_symbol_name}_status.json"
    log_file = f"{safe_symbol_name}_log.csv"
    model_file = f"models/{safe_symbol_name}_h4.pkl"

    data_svc = DataService(api_key=config['exchange']['api_key'], api_secret=config['exchange']['api_secret'])
    telegram_svc = TelegramService(bot_token=config['telegram']['bot_token'], channel_id=config['telegram']['channel_id'])
    
    trade_manager = TradeManagerService(data_svc, telegram_svc, log_file, status_file, symbol)
    trade_manager.check_open_trade()

    try:
        with open(status_file, 'r') as f:
            status = json.load(f)
    except FileNotFoundError:
        with open(status_file, 'w') as f:
            json.dump({"is_trade_open": False, "current_trade": {}}, f, indent=2)
        status = {"is_trade_open": False}

    if status.get('is_trade_open', False):
        print(f"{strategy_name}: A trade is already open. Skipping new signal analysis.")
        return

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


def run_daily_recap(config):
    print("\n" + "="*50)
    print(f"[{datetime.now()}] --- Daily Recap is currently disabled ---")
    print("="*50)


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')

    if 'YOUR_TELEGRAM_BOT_TOKEN_HERE' in config['telegram']['bot_token']:
        print("FATAL ERROR: Please set your Telegram bot token in config.ini before running.")
        exit()

    symbols_to_trade = [symbol.strip() for symbol in config['parameters']['symbols'].split(',')]
    
    print("\n" + "="*50)
    print("--- Running the first cycle manually for all strategies on startup ---")
    print("="*50)
    
    for symbol in symbols_to_trade:
        run_trade_cycle_for_symbol(config, symbol)

    print("\n" + "="*50)
    print("--- First manual cycle finished ---")
    print("="*50)
    
    print("\n--- Initializing Market-Aware Scheduler for all future cycles ---")
    scheduler = BlockingScheduler(timezone="UTC")
    
    # Create a separate job for each symbol
    for symbol in symbols_to_trade:
        safe_symbol_name = symbol.replace('/', '_').lower()
        scheduler.add_job(
            run_trade_cycle_for_symbol, 
            'cron', 
            hour='0,4,8,12,16,20', 
            minute=1, 
            args=[config, symbol],
            id=f'swing_{safe_symbol_name}'
        )
    
    print("\nMarket-Aware Bot Scheduler Started:")
    print("  - H4 Swing Bot for all symbols will run on the 4-hour marks.")
    print("The bot is now running. Press Ctrl+C to exit.")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")