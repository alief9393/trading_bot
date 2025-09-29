import pandas as pd
import pandas_ta as ta

class IndicatorService:
    """
    Service responsible for calculating the specific suite of indicators
    that the final, best-performing AI models were trained on.
    """
    def __init__(self):
        print("IndicatorService: Initialized.")

    def add_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            print("IndicatorService: Input DataFrame is empty. Cannot add indicators.")
            return df
            
        print("IndicatorService: Calculating the final, optimized suite of indicators...")
        
        # --- 1. Ichimoku Cloud ---
        # This was proven to be a valuable addition.
        ichimoku_df, _ = ta.ichimoku(
            high=df['high'], 
            low=df['low'], 
            close=df['close'],
            tenkan=9, 
            kijun=26, 
            senkou=52
        )
        ichimoku_df.rename(columns={
            'ITS_9': 'ichimoku_tenkan_sen',
            'IKS_26': 'ichimoku_kijun_sen',
            'ISA_9': 'ichimoku_senkou_span_a',
            'ISB_26': 'ichimoku_senkou_span_b',
            'ICS_26': 'ichimoku_chikou_span'
        }, inplace=True)
        df = pd.concat([df, ichimoku_df], axis=1)

        # --- 2. Core Trend, Volatility, and Momentum Indicators ---
        # These are the foundational indicators that the models consistently found useful.
        df.ta.ema(length=21, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.sma(length=200, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.atr(length=14, append=True)
        df.ta.adx(length=14, append=True)
        df.ta.squeeze(lazy_bear=True, append=True)

        # --- 3. Final Cleanup ---
        # Drop all rows with NaN values that were created during the indicator calculations
        df.dropna(inplace=True)
        
        print("IndicatorService: Final, optimized indicator suite successfully added.")
        return df