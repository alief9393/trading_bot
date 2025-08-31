# services/telegram_service.py
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
            print(f"TelegramService: Error initializing bot: {e}")
            self.bot = None

    def send_text_message(self, message: str):
        """A simple helper method to send any text message."""
        if not self.bot: return
        try:
            self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"TelegramService: An error occurred while sending message: {e}")


    def send_signal(self, trade_signal: dict, symbol: str):
        decision = trade_signal['decision']
        entry = trade_signal['entry']
        sl = trade_signal['sl']
        tp1 = trade_signal['tp1']
        tp2 = trade_signal['tp2']
        tp3 = trade_signal['tp3']
        rationale = trade_signal['rationale']

        signal_emoji = "🚀" if decision == "BUY" else "🔻"
        header = f"{signal_emoji} **New H4 Signal** {signal_emoji}"
        
        message = (
            f"{header}\n\n"
            f"**Pair:** {symbol}\n"
            f"**Decision:** **{decision}**\n\n"
            f"**Entry Price:** `{entry}`\n\n"
            f"🟢 **Take Profit 1:** `{tp1}`\n"
            f"🟢 **Take Profit 2:** `{tp2}`\n"
            f"🟢 **Take Profit 3:** `{tp3}`\n\n"
            f"🔴 **Stop Loss:** `{sl}`\n\n"
            f"**Automated Rationale:**\n"
            f"_{rationale}_"
        )
        self.send_text_message(message)
        print(f"TelegramService: Successfully sent {decision} signal for {symbol} to channel.")
    
    def send_market_update(self, status: str, reason: str = None):
        message = ""
        if status == "hold":
            message = (
                "🧠 **Autonomous Market Update (No Signal)**\n\n"
                "The market conditions are not optimal for a new entry at this time. Our AI has predicted **HOLD** for this cycle.\n\n"
                "_Strategy: Patience. We are protecting capital by waiting for a higher-probability setup._"
            )
        elif status == "veto":
            message = (
                "🧠 **Autonomous Market Update (Signal Vetoed)**\n\n"
                "Our AI identified a potential signal, but it was **vetoed** by our risk management rules.\n\n"
                f"**Reason:** _{reason}_\n\n"
                "_Strategy: Discipline. We avoid lower-quality signals to protect capital._"
            )
        if message:
            self.send_text_message(message)
            print("TelegramService: Successfully sent market update.")

    # Note: The daily recap would need to be re-designed to read multiple log files.
    # It has been disabled in the main scheduler for now to keep things simple.