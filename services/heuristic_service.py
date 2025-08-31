import pandas as pd

class HeuristicService:
    """
    Service for applying validation rules, risk management, and generating
    the final trade signal object (the "Glass Box" logic).
    """
    def __init__(self):
        print("HeuristicService: Initialized.")

    def generate_trade_signal(self, prediction: int, df: pd.DataFrame) -> dict:
        """
        Validates an AI prediction and, if valid, constructs a complete trade signal
        with multiple Take Profit levels based on market volatility (ATR).
        """
        if df is None or df.empty:
            return {"status": "error", "reason": "No market data available."}
        
        if prediction == 0:
            return {"status": "hold"}
    
        latest_candle = df.iloc[-1]
    
        # --- Heuristic Validation Rules (Stays the same) ---
        print("HeuristicService: Applying validation rules...")
        if prediction == 1: # AI wants to BUY
            if latest_candle['close'] < latest_candle['EMA_50']:
                return {"status": "veto", "reason": "Price is below the 50-period EMA, suggesting bearish conditions."}
        elif prediction == -1: # AI wants to SELL
            if latest_candle['close'] > latest_candle['EMA_50']:
                return {"status": "veto", "reason": "Price is above the 50-period EMA, suggesting bullish conditions."}

        # --- Risk Management Overlay (Stays the same) ---
        print("HeuristicService: Applying risk management rules...")
        atr_value = latest_candle['ATRr_14']
        max_allowable_atr = latest_candle['close'] * 0.05 
        if atr_value > max_allowable_atr:
            return {"status": "veto", "reason": f"Extreme market volatility detected (ATR is too high)."}
    
        # --- NEW: Dynamic TP/SL Calculation based on ATR ---
        print("HeuristicService: All checks passed. Constructing signal with multiple TPs.")
        
        entry_price = latest_candle['close']
        rationale = "Signal confirmed by market structure and momentum indicators."
        
        if prediction == 1: # BUY Signal
            decision = "BUY"
            # Stop Loss is set at 2x ATR below the entry
            stop_loss = entry_price - (2 * atr_value)
            # TP1 is set at 2x ATR above entry (1:1 Risk/Reward)
            take_profit_1 = entry_price + (2 * atr_value)
            # TP2 is set at 4x ATR above entry (1:2 Risk/Reward)
            take_profit_2 = entry_price + (4 * atr_value)
            # TP3 is set at 6x ATR above entry (1:3 Risk/Reward)
            take_profit_3 = entry_price + (6 * atr_value)
            
        else: # SELL Signal
            decision = "SELL"
            # Stop Loss is set at 2x ATR above the entry
            stop_loss = entry_price + (2 * atr_value)
            # TP1 is set at 2x ATR below entry (1:1 Risk/Reward)
            take_profit_1 = entry_price - (2 * atr_value)
            # TP2 is set at 4x ATR below entry (1:2 Risk/Reward)
            take_profit_2 = entry_price - (4 * atr_value)
            # TP3 is set at 6x ATR below entry (1:3 Risk/Reward)
            take_profit_3 = entry_price - (6 * atr_value)

        trade_signal = {
            "decision": decision,
            "entry": round(entry_price, 2),
            "sl": round(stop_loss, 2),
            "tp1": round(take_profit_1, 2),
            "tp2": round(take_profit_2, 2),
            "tp3": round(take_profit_3, 2),
            "rationale": rationale
        }
    
        return {"status": "success", "signal": trade_signal} 