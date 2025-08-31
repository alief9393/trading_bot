# services/trade_logger.py (The NEW Upgraded Version)

import csv
from datetime import datetime
import os

class TradeLogger:
    def __init__(self, filename: str):
        self.filename = filename
        self.file_exists = os.path.isfile(self.filename)
        self.init_log_file()

    def init_log_file(self):
        """Creates the CSV file with headers if it doesn't exist."""
        if not self.file_exists:
            with open(self.filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # --- NEW HEADERS ---
                writer.writerow([
                    "Signal_Time", "Symbol", "Decision", "Entry_Price", 
                    "Take_Profit_1", "Take_Profit_2", "Take_Profit_3", "Stop_Loss", 
                    "Outcome", "Exit_Time", "Exit_Price", "Profit_Pips"
                ])
                # -----------------
            print(f"TradeLogger: Created new log file '{self.filename}' with updated columns.")

    def log_new_signal(self, symbol: str, signal: dict):
        """Logs a new, open trade signal to the CSV file with multiple TPs."""
        with open(self.filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # --- NEW LOGGING LOGIC ---
            writer.writerow([
                datetime.now().strftime("%Y-m-d %H:%M:%S"),
                symbol,
                signal['decision'],
                signal['entry'],
                signal['tp1'],       # Use 'tp1'
                signal['tp2'],       # Use 'tp2'
                signal['tp3'],       # Use 'tp3'
                signal['sl'],        # Use 'sl'
                "OPEN",
                "",
                "",
                ""
            ])
            # -------------------------
        print(f"TradeLogger: Logged new {signal['decision']} signal for {symbol}.")