# services/heuristic_service.py (The FINAL MTF Version)

import pandas as pd

class HeuristicService:
    def __init__(self):
        print("HeuristicService: Initialized with MTF Logic.")

    def generate_h4_bias(self, prediction: int, df: pd.DataFrame) -> dict:
        """
        The "General": Analyzes the H4 chart to establish a strategic bias and a zone of interest.
        """
        if df is None or df.empty:
            return {"status": "error"}
        
        if prediction == 0:
            return {"status": "hold"}
    
        latest_candle = df.iloc[-1]
        
        if prediction == 1 and latest_candle['close'] < latest_candle['EMA_50']:
            return {"status": "veto", "reason": "Bullish AI signal is below the H4 50 EMA."}
        if prediction == -1 and latest_candle['close'] > latest_candle['EMA_50']:
            return {"status": "veto", "reason": "Bearish AI signal is above the H4 50 EMA."}

        # The bias is valid. Now, define the tactical plan.
        atr_value = latest_candle['ATRr_14']
        pullback_level = latest_candle['EMA_21'] # The optimal entry is a pullback to the 21 EMA.
        
        if prediction == 1:
            decision = "BUY"
            stop_loss = pullback_level - (2 * atr_value)
            take_profit_1 = pullback_level + (2 * atr_value)
            take_profit_2 = pullback_level + (4 * atr_value)
            take_profit_3 = pullback_level + (6 * atr_value)
        else: # SELL
            decision = "SELL"
            stop_loss = pullback_level + (2 * atr_value)
            take_profit_1 = pullback_level - (2 * atr_value)
            take_profit_2 = pullback_level - (4 * atr_value)
            take_profit_3 = pullback_level - (6 * atr_value)

        bias_details = {
            "bias": decision,
            "pullback_level": round(pullback_level, 2),
            "sl": round(stop_loss, 2),
            "tp1": round(take_profit_1, 2),
            "tp2": round(take_profit_2, 2),
            "tp3": round(take_profit_3, 2),
            "rationale": "H4 trend confirmed by AI. Awaiting H1 confirmation."
        }
    
        return {"status": "success", "bias_details": bias_details}

    def confirm_h1_entry(self, df: pd.DataFrame, bias: str) -> bool:
        """
        The "Scout": Analyzes the last closed H1 candle for a specific confirmation pattern.
        """
        if df is None or len(df) < 2:
            return False # Need at least two candles for pattern recognition
            
        last_candle = df.iloc[-1]
        
        # Check for a Bullish Confirmation (if our bias is BUY)
        if bias == "BUY":
            # Bullish Engulfing Pattern
            is_bullish_engulfing = (last_candle['close'] > last_candle['open'] and 
                                    last_candle['open'] < df.iloc[-2]['close'] and 
                                    last_candle['close'] > df.iloc[-2]['open'])
            # Hammer Pattern (strong close at the top of the range)
            is_hammer = (last_candle['close'] - last_candle['low']) / (last_candle['high'] - last_candle['low']) > 0.7

            if is_bullish_engulfing or is_hammer:
                print("HeuristicService (Scout): H1 Bullish entry pattern CONFIRMED.")
                return True

        # Check for a Bearish Confirmation (if our bias is SELL)
        elif bias == "SELL":
            # Bearish Engulfing Pattern
            is_bearish_engulfing = (last_candle['close'] < last_candle['open'] and 
                                    last_candle['open'] > df.iloc[-2]['close'] and 
                                    last_candle['close'] < df.iloc[-2]['open'])
            # Shooting Star Pattern (strong close at the bottom of the range)
            is_shooting_star = (last_candle['high'] - last_candle['close']) / (last_candle['high'] - last_candle['low']) > 0.7

            if is_bearish_engulfing or is_shooting_star:
                print("HeuristicService (Scout): H1 Bearish entry pattern CONFIRMED.")
                return True
        
        return False