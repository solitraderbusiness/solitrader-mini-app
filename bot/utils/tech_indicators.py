"""
Technical-indicator helpers for TG-Trade Suite
Build a quick snapshot (RSI, MACD, …) for the current dataframe.
"""

from __future__ import annotations

import logging
from typing import Dict, List

import numpy as np

# ----------------------------------------------------------------------
#  PATCH for NumPy 2  → add the legacy alias that pandas-ta requires
# ----------------------------------------------------------------------
if not hasattr(np, "NaN"):  # NumPy <2 has it, NumPy 2 removed it
    np.NaN = np.nan  # type: ignore[attr-defined]  # noqa: N806

import pandas as pd
import pandas_ta as ta  # noqa: E402  (import after patch)

logger = logging.getLogger(__name__)


def _fmt(value: float, digits: int = 2) -> str:
    """Human-friendly float formatting."""
    return f"{value:.{digits}f}"


def build_indicator_snapshot(df: pd.DataFrame) -> str:
    """
    Return a short, bullet-point text block with popular indicators that
    will be appended to the OpenAI prompt.

    Parameters
    ----------
    df
        OHLCV dataframe produced by ``data_fetcher.fetch_ohlcv``.
        **Index must be in chronological order (oldest → newest).**

    Returns
    -------
    str
        Ready-for-prompt, markdown-friendly text.
    """
    # Safety – need at least ~100 bars for most indicators
    if len(df) < 120:
        logger.warning("Not enough data for indicators – rows=%d", len(df))
        return "No live indicators – insufficient history."

    close = df["close"]

    # --- Simple indicators ------------------------------------------------
    rsi = ta.rsi(close, length=14).iloc[-1]
    macd = ta.macd(close, fast=12, slow=26, signal=9)
    macd_hist = macd["MACDh_12_26_9"].iloc[-1]
    bb = ta.bbands(close, length=20)
    bb_perc = bb["BBP_20_2.0"].iloc[-1] * 100  # % position in the band

    indicator_lines: List[str] = [
        f"• **RSI (14)**: {_fmt(rsi)}",
        f"• **MACD hist.**: {_fmt(macd_hist)}",
        f"• **BB% (20-2σ)**: {_fmt(bb_perc)} %",
    ]

    # --- Trend detection (200-SMA vs price) -------------------------------
    sma200 = ta.sma(close, length=200).iloc[-1]
    trend = "↑ Uptrend" if close.iloc[-1] > sma200 else "↓ Downtrend"
    indicator_lines.append(f"• **Trend (200-SMA)**: {trend}")

    # You can add more metrics here (ATR, ADX, …) as needed
    logger.info("✅ Indicator snapshot built")
    return "\n".join(indicator_lines)

