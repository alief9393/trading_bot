# services/indicator_service.py (The FINAL, Enhanced Version)

import pandas as pd
import pandas_ta as ta

class IndicatorService:
    """
    Service responsible for calculating a full suite of basic and advanced
    technical indicators for the AI model.
    """
    def __init__(self):
        print("IndicatorService: Initialized.")

    def add_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            print("IndicatorService: Input DataFrame is empty. Cannot add indicators.")
            return df
            
        print("IndicatorService: Calculating and adding a full suite of technical indicators...")
        
        # --- 1. Create a full Ichimoku Cloud analysis ---
        # The ta.ichimoku method returns a new DataFrame, so we calculate it separately
        # and then merge it into our main DataFrame.
        ichimoku_df, _ = ta.ichimoku(
            high=df['high'], 
            low=df['low'], 
            close=df['close'],
            tenkan=9, 
            kijun=26, 
            senkou=52
        )
        # Rename the default columns for clarity
        ichimoku_df.rename(columns={
            'ITS_9': 'ichimoku_tenkan_sen',
            'IKS_26': 'ichimoku_kijun_sen',
            'ISA_9': 'ichimoku_senkou_span_a',
            'ISB_26': 'ichimoku_senkou_span_b',
            'ICS_26': 'ichimoku_chikou_span'
        }, inplace=True)
        # Join the new Ichimoku columns to the main DataFrame
        df = pd.concat([df, ichimoku_df], axis=1)

        # --- 2. Add all other standard and advanced indicators using the .ta extension ---
        
        # Original indicators (keeping them)
        df.ta.ema(length=21, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.sma(length=200, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.atr(length=14, append=True)
        df.ta.adx(length=14, append=True)

        # --- 3. Add the Squeeze Momentum Indicator ---
        # This is a powerful indicator for detecting breakouts.
        # lazy_bear=True uses a popular, well-regarded version of the calculation.
        df.ta.squeeze(lazy_bear=True, append=True)

        # --- 4. Final Cleanup ---
        # Drop all rows with NaN values that were created during the indicator calculations
        df.dropna(inplace=True)
        
        print("IndicatorService: All indicators successfully calculated and added.")
        return df