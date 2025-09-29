# trading_bot/services/heuristic_service.py (The FINAL, Definitive Version)

import pandas as pd

class HeuristicService:
    def __init__(self):
        print("HeuristicService: Initialized with definitive AI-centric logic.")

    def generate_h4_bias(self, prediction: int, df: pd.DataFrame) -> dict:
        """
        The "General": Takes the AI's prediction and generates a tactical plan.
        This version trusts the AI and does not use a simple EMA veto.
        """
        if df is None or df.empty:
            print("HeuristicService: Received empty DataFrame. Cannot generate bias.")
            return {"status": "error"}
        
        if prediction == 0:
            print("HeuristicService: Received HOLD prediction (0). No bias generated.")
            return {"status": "hold"}
    
        print("HeuristicService: Received valid AI prediction. Generating tactical plan...")
        latest_candle = df.iloc[-1]
        
        # --- The simple EMA_50 Veto rule has been permanently removed ---
        # We now fully trust the judgment of our highly-tuned AI models.
        
        atr_value = latest_candle['ATRr_14']
        pullback_level = latest_candle['EMA_21']
        
        if prediction == 1:
            decision = "BUY"
            stop_loss = pullback_level - (2 * atr_value)
            take_profit_1 = pullback_level + (2 * atr_value)
            take_profit_2 = pullback_level + (4 * atr_value)
            take_profit_3 = pullback_level + (6 * atr_value)
        else: # prediction == -1
            decision = "SELL"
            stop_loss = pullback_level + (2 * atr_value)
            take_profit_1 = pullback_level - (2 * atr_value)
            take_profit_2 = pullback_level - (4 * atr_value)
            take_profit_3 = pullback_level - (6 * atr_value)

        bias_details = {
            "bias": decision,
            "pullback_level": round(pullback_level, 2), # Rounded for Crypto precision
            "sl": round(stop_loss, 2),
            "tp1": round(take_profit_1, 2),
            "tp2": round(take_profit_2, 2),
            "tp3": round(take_profit_3, 2),
            "rationale": "H4 bias confirmed by AI. Awaiting H1 confirmation."
        }
    
        print(f"HeuristicService: Successfully generated {decision} bias.")
        return {"status": "success", "bias_details": bias_details}

    def confirm_h1_entry(self, df: pd.DataFrame, bias: str) -> bool:
        """
        The "Scout": Analyzes the last closed H1 candle for a confirmation pattern.
        """
        if df is None or len(df) < 2:
            return False
            
        last_candle = df.iloc[-1]
        
        if bias == "BUY":
            is_bullish_engulfing = (last_candle['close'] > last_candle['open'] and 
                                    last_candle['open'] < df.iloc[-2]['close'] and 
                                    last_candle['close'] > df.iloc[-2]['open'])
            is_hammer = (last_candle['close'] - last_candle['low']) / (last_candle['high'] - last_candle['low']) > 0.7
            if is_bullish_engulfing or is_hammer:
                print("HeuristicService (Scout): H1 Bullish entry pattern CONFIRMED.")
                return True

        elif bias == "SELL":
            is_bearish_engulfing = (last_candle['close'] < last_candle['open'] and 
                                    last_candle['open'] > df.iloc[-2]['close'] and 
                                    last_candle['close'] < df.iloc[-2]['open'])
            is_shooting_star = (last_candle['high'] - last_candle['close']) / (last_candle['high'] - last_candle['low']) > 0.7
            if is_bearish_engulfing or is_shooting_star:
                print("HeuristicService (Scout): H1 Bearish entry pattern CONFIRMED.")
                return True
        
        return False