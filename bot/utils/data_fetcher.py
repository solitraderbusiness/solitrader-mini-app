import os, time, finnhub, pandas as pd

import logging

_FINN = finnhub.Client(api_key=os.getenv("FINNHUB_API_KEY"))

logger = logging.getLogger(__name__)

# mapping chat “1h, 4h, 1d …” -> Finnhub res string
RES = {"1m":"1", "5m":"5", "15m":"15", "30m":"30",
       "1h":"60", "4h":"240", "1d":"D", "1w":"W"}

def fetch_ohlcv(symbol: str, tf: str, lookback_days: int = 180) -> pd.DataFrame:
    """Return a dataframe with utc timestamp index and OHLCV cols."""
    now = int(time.time())
    _from = now - lookback_days * 24 * 3600
    res = _FINN.crypto_candles(symbol, RES[tf], _from, now)


    # 📡  Log the outbound call so it shows up in docker logs
    logger.info(
         "📡 Finnhub call: symbol=%s tf=%s lookback=%d d status=%s rows=%s",
         symbol, tf, lookback_days,
         res.get("s", "?"),
         len(res.get("t", [])),
     )




    if res["s"] != "ok":
        raise RuntimeError(f"Finnhub error: {res}")
    df = pd.DataFrame(res)[["t","o","h","l","c","v"]]
    df.columns = ["ts","open","high","low","close","volume"]
    df["ts"] = pd.to_datetime(df["ts"], unit="s", utc=True)
    return df.set_index("ts")

