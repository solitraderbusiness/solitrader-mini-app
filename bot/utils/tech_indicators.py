import pandas_ta as ta

def add_indicators(df):
    df = df.copy()
    df.ta.ema(length=50, append=True)      # EMA_50
    df.ta.ema(length=200, append=True)     # EMA_200
    df.ta.rsi(length=14, append=True)      # RSI_14
    df.ta.macd(append=True)                # MACD_12_26_9, etc.
    df.ta.bbands(length=20, append=True)   # BB_L_BB_M_BB_U
    df.ta.atr(length=14, append=True)
    return df

