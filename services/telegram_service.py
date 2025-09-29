import telegram
import pandas as pd
from datetime import datetime

class TelegramService:
    def __init__(self, bot_token: str, channel_id: str):
        try:
            self.bot = telegram.Bot(token=bot_token)
            self.channel_id = channel_id
            print("TelegramService: Bot initialized successfully.")
        except Exception as e:
            self.bot = None

    def send_text_message(self, message: str):
        if not self.bot: return
        try:
            self.bot.send_message(chat_id=self.channel_id, text=message, parse_mode='Markdown')
        except Exception as e:
            print(f"TelegramService: An error occurred while sending message: {e}")

    def send_bias_alert(self, bias_details: dict, symbol: str):
        bias = bias_details['bias']
        pullback_level = bias_details['pullback_level']
        header = "🎯 **New H4 Bias Detected** 🎯"
        
        message = (
            f"{header}\n\n"
            f"**Pair:** {symbol}\n"
            f"**Strategic Bias:** {bias}\n\n"
            f"The bot is now switching to the H1 chart to hunt for a precise entry around the **`{pullback_level}`** level.\n\n"
            "_No action is needed. A final execution alert will be sent if an entry is confirmed._"
        )
        self.send_text_message(message)
        print(f"TelegramService: Successfully sent H4 Bias alert for {symbol}.")

    def send_execution_alert(self, trade_details: dict, symbol: str):
        decision = trade_details['bias']
        entry = trade_details['entry']
        sl = trade_details['sl']
        tp1 = trade_details['tp1']
        tp2 = trade_details['tp2']
        tp3 = trade_details['tp3']
        signal_emoji = "🚀" if decision == "BUY" else "🔻"
        header = f"{signal_emoji} **H1 Entry Confirmed: Trade Executed** {signal_emoji}"
        
        message = (
            f"{header}\n\n"
            f"**Pair:** {symbol}\n"
            f"**Decision:** **{decision}**\n\n"
            f"**Entry Price:** `{entry}`\n\n"
            f"🟢 **Take Profit 1:** `{tp1}`\n"
            f"🟢 **Take Profit 2:** `{tp2}`\n"
            f"🟢 **Take Profit 3:** `{tp3}`\n\n"
            f"🔴 **Stop Loss:** `{sl}`"
        )
        self.send_text_message(message)
        print(f"TelegramService: Successfully sent final execution alert for {symbol}.")