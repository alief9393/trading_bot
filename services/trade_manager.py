# services/trade_manager.py
import pandas as pd
import json

class TradeManagerService:
    def __init__(self, data_svc, telegram_svc, trade_log_file: str, status_file: str, symbol: str):
        self.data_svc = data_svc
        self.telegram_svc = telegram_svc
        self.trade_log_file = trade_log_file
        self.status_file = status_file
        self.symbol = symbol
        print(f"TradeManagerService for H4 {self.symbol} Initialized.")

    def check_open_trade(self):
        try:
            with open(self.status_file, 'r') as f:
                status = json.load(f)
        except FileNotFoundError:
            return

        if not status.get('is_trade_open', False):
            return

        print(f"TradeManagerService ({self.symbol}): Open trade detected. Checking status...")
        trade = status['current_trade']
        
        # We can fetch a faster timeframe like M1 for more precise checking
        latest_data = self.data_svc.get_market_data(symbol=self.symbol, timeframe='1m', limit=2)
        if latest_data is None or latest_data.empty:
            print(f"TradeManagerService ({self.symbol}): Could not fetch latest market data to check trade.")
            return
            
        current_high = latest_data.iloc[-1]['high']
        current_low = latest_data.iloc[-1]['low']
        
        outcome, exit_price = "OPEN", None

        if trade['decision'] == 'BUY':
            if current_low <= trade['sl']: outcome, exit_price = "SL", trade['sl']
            elif current_high >= trade.get('tp3', float('inf')): outcome, exit_price = "TP3", trade['tp3']
            elif current_high >= trade.get('tp2', float('inf')): outcome, exit_price = "TP2", trade['tp2']
            elif current_high >= trade.get('tp1', float('inf')): outcome, exit_price = "TP1", trade['tp1']
        elif trade['decision'] == 'SELL':
            if current_high >= trade['sl']: outcome, exit_price = "SL", trade['sl']
            elif current_low <= trade.get('tp3', float('-inf')): outcome, exit_price = "TP3", trade['tp3']
            elif current_low <= trade.get('tp2', float('-inf')): outcome, exit_price = "TP2", trade['tp2']
            elif current_low <= trade.get('tp1', float('-inf')): outcome, exit_price = "TP1", trade['tp1']
        
        if outcome != "OPEN":
            print(f"TradeManagerService ({self.symbol}): {outcome} hit for {trade['decision']} trade at {exit_price}")
            self.finalize_trade(trade, outcome, exit_price)

    def finalize_trade(self, trade, outcome, exit_price):
        message = f"🔔 **Trade Update ({self.symbol})** 🔔\n\nOur **{trade['decision']}** trade has hit **{outcome}** at `{exit_price}`!"
        
        try:
            # We will use the simplified send_text_message method
            self.telegram_svc.send_text_message(message)
        except Exception as e:
            print(f"TradeManagerService: Failed to send Telegram update: {e}")

        new_status = {"is_trade_open": False, "current_trade": {}}
        with open(self.status_file, 'w') as f:
            json.dump(new_status, f, indent=2)
        print(f"TradeManagerService ({self.symbol}): Trade closed. Bot memory at '{self.status_file}' has been reset.")