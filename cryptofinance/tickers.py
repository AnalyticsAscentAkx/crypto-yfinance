"""
cryptofinance.tickers
~~~~~~~~~~~~~~~~~~~~~
Multi-asset helpers: Tickers class and the module-level download() function.
"""

import logging
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from .ticker import Ticker
from .utils.get_history import get_history
from .utils.validation import split_pair

logger = logging.getLogger("cryptofinance")


class Tickers:
    """Wrapper around a collection of Ticker objects.

    Parameters
    ----------
    symbols : list or space/comma-separated string of symbols
              e.g. ``['BTC_USD', 'ETH_USD', 'SOL_USD']``
              or   ``'BTC_USD ETH_USD SOL_USD'``

    Examples
    --------
    >>> from cryptofinance import Tickers
    >>> t = Tickers(['BTC_USD', 'ETH_USD', 'SOL_USD'])
    >>> t.history(days=30)            # combined OHLCV DataFrame
    >>> t['BTC_USD'].info             # access individual Ticker
    >>> t.prices()                    # dict of current prices
    """

    def __init__(self, symbols):
        if isinstance(symbols, str):
            symbols = symbols.replace(",", " ").split()
        self._symbols = list(dict.fromkeys("_".join(split_pair(s)).lower() for s in symbols))
        self.tickers: dict[str, Ticker] = {s: Ticker(s) for s in self._symbols}

    def __getitem__(self, symbol: str) -> Ticker:
        return self.tickers["_".join(split_pair(symbol)).lower()]

    def __iter__(self):
        return iter(self.tickers.values())

    def __repr__(self) -> str:
        return f"Tickers({[s.upper() for s in self._symbols]})"

    # ── Data methods ──────────────────────────────────────────────────────

    def history(self, days: int = 30, interval: str = "daily") -> pd.DataFrame:
        """Fetch OHLCV for all symbols and return a combined multi-level DataFrame.

        The result has a two-level column index: (field, symbol).
        e.g. ``df['close']['BTC_USD']``
        """
        if not self._symbols:
            return pd.DataFrame()
        frames = {}
        metadata = {}

        def _fetch(sym):
            return sym, get_history(sym, days=days, interval=interval)

        with ThreadPoolExecutor(max_workers=min(len(self._symbols), 6)) as pool:
            futures = [pool.submit(_fetch, sym) for sym in self._symbols]
            for fut in as_completed(futures):
                sym, df = fut.result()
                metadata[sym.upper()] = dict(df.attrs)
                df = df.set_index("timestamp")
                df.attrs = {}
                frames[sym.upper()] = df

        if not frames:
            return pd.DataFrame()

        symbols = [s.upper() for s in self._symbols]
        combined = pd.concat([frames[s] for s in symbols], keys=symbols, axis=1)
        combined = combined.swaplevel(0, 1, axis=1)
        fields = ["open", "high", "low", "close", "volume"]
        combined = combined.reindex(columns=pd.MultiIndex.from_product([fields, symbols], names=["field", "symbol"]))
        combined.attrs["sources"] = metadata
        return combined

    def prices(self) -> dict:
        """Return current price for every symbol as a plain dict."""
        result = {}
        for sym, ticker in self.tickers.items():
            try:
                result[sym.upper()] = ticker.price
            except Exception as exc:
                logger.warning("Price unavailable for %s: %s", sym, exc)
                result[sym.upper()] = None
        return result

    def fast_info(self) -> pd.DataFrame:
        """Return a summary table of fast_info for all symbols."""
        rows = []
        for sym, ticker in self.tickers.items():
            try:
                row = ticker.fast_info
                row["symbol"] = sym.upper()
                rows.append(row)
            except Exception as exc:
                logger.warning("Coin profile unavailable for %s: %s", sym, exc)
        return pd.DataFrame(rows).set_index("symbol") if rows else pd.DataFrame()

    def plot(self, days: int = 90, theme: str = "plotly_dark", show: bool = True):
        """Compare all assets as indexed returns and return a Plotly figure."""
        from .utils.plots import plot_compare
        return plot_compare(
            [symbol.upper() for symbol in self._symbols],
            days=days,
            theme=theme,
            show=show,
        )

    def correlation(self, days: int = 90, theme: str = "plotly_dark", show: bool = True):
        """Plot the return-correlation matrix for all assets."""
        from .utils.plots import plot_correlation
        return plot_correlation(
            [symbol.upper() for symbol in self._symbols],
            days=days,
            theme=theme,
            show=show,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Module-level download() — mirrors yfinance.download()
# ─────────────────────────────────────────────────────────────────────────────

def download(
    symbols,
    days: int = 30,
    interval: str = "daily",
) -> pd.DataFrame:
    """Batch-download OHLCV history for one or more symbols.

    This is the module-level equivalent of ``yfinance.download()``.

    Parameters
    ----------
    symbols  : single symbol string or list of symbols
               e.g. ``'BTC_USD'`` or ``['BTC_USD', 'ETH_USD', 'SOL_USD']``
    days     : days of history (default 30)
    interval : ``'daily'``, ``'hourly'``, ``'4h'``, ``'15m'``

    Returns
    -------
    - Single symbol → simple DataFrame (timestamp, open, high, low, close, volume)
    - Multiple symbols → multi-level DataFrame with (field, symbol) column index

    Examples
    --------
    >>> from cryptofinance import download
    >>> df = download('BTC_USD', days=90)
    >>> df = download(['BTC_USD', 'ETH_USD', 'SOL_USD'], days=30)
    >>> df['close']['BTC_USD']
    """
    if isinstance(symbols, str):
        parts = symbols.replace(",", " ").split()
        if len(parts) == 1:
            return get_history(parts[0], days=days, interval=interval)
        symbols = parts

    return Tickers(symbols).history(days=days, interval=interval)
