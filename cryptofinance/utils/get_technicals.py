import pandas as pd
from .get_history import get_history


def get_technicals(symbol: str, days: int = 90) -> pd.DataFrame:
    """Return OHLCV data enriched with technical indicators.

    Requires ``pandas-ta-classic``. Install it with::

        pip install "crypto-yfinance[ta]"

    Parameters
    ----------
    symbol : e.g. ``'BTC_USD'``, ``'ETH_USD'``
    days   : days of history to use as the base (default 90)

    Returns
    -------
    DataFrame with all OHLCV columns plus:

    **Trend**
        - ``EMA_20``, ``EMA_50``, ``SMA_200``
    **Momentum**
        - ``RSI_14`` — 0-100, overbought >70, oversold <30
        - ``MACD``, ``MACDh`` (histogram), ``MACDs`` (signal)
    **Volatility**
        - ``BBL_20`` (lower band), ``BBM_20`` (mid), ``BBU_20`` (upper)
        - ``ATRr_14`` — Average True Range
    **Volume**
        - ``OBV`` — On-Balance Volume
    """
    try:
        import pandas_ta_classic as ta
    except ImportError:
        try:
            import pandas_ta as ta
        except ImportError as exc:
            raise ImportError(
                "pandas-ta-classic is required for technical indicators.\n"
                "Install it with:  pip install 'crypto-yfinance[ta]'"
            ) from exc

    df = get_history(symbol, days=max(days, 210), interval="daily")
    df = df.set_index("timestamp").copy()

    # Trend
    df.ta.ema(length=20, append=True)
    df.ta.ema(length=50, append=True)
    df.ta.sma(length=200, append=True)

    # Momentum
    df.ta.rsi(length=14, append=True)
    df.ta.macd(fast=12, slow=26, signal=9, append=True)

    # Volatility
    df.ta.bbands(length=20, std=2, append=True)
    df.ta.atr(length=14, append=True)

    # Volume
    df.ta.obv(append=True)

    # Return only the requested window
    df = df.tail(days).reset_index()
    return df
