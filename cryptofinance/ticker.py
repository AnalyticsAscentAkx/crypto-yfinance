"""
cryptofinance.ticker
~~~~~~~~~~~~~~~~~~~~
The Ticker class — a single-asset wrapper that bundles all data
functions into one clean interface, similar to yfinance's Ticker.
"""

from typing import Optional
import pandas as pd
from .utils.validation import split_pair

from .utils.get_price import get_price
from .utils.get_history import get_history
from .utils.get_market_cap import get_market_cap
from .utils.get_volume import get_volume
from .utils.get_info import get_info
from .utils.get_dominance import get_dominance
from .utils.get_funding_rate import get_funding_rate
from .utils.get_open_interest import get_open_interest
from .utils.get_long_short import get_long_short_ratio
from .utils.get_onchain import get_onchain
from .utils.get_news import get_news
from .utils.get_technicals import get_technicals
from .utils.plot_price import plot_price
from .utils.coingecko_resolver import register_coin, resolve_cg_id
from .utils.search_symbol import search_symbol


class Ticker:
    """Single-asset data wrapper for crypto.

    Parameters
    ----------
    symbol : asset pair in ``BASE_QUOTE`` format, e.g. ``'BTC_USD'``, ``'ETH_USDT'``

    Examples
    --------
    >>> from cryptofinance import Ticker
    >>> t = Ticker('BTC_USD')
    >>> t.history(days=30)
    >>> t.info
    >>> t.funding_rate
    >>> t.onchain
    >>> t.plot()
    """

    def __init__(self, symbol: str):
        self._symbol = "_".join(split_pair(symbol)).lower()

    @classmethod
    def from_name(cls, query: str, quote: str = "USD"):
        """Create a ticker by searching a coin name, symbol, or CoinGecko ID.

        This supports newly launched coins without waiting for a package update.
        The highest-ranked exact match is selected.
        """
        matches = search_symbol(query, quote=quote, limit=1)
        if not matches:
            raise ValueError(f"No cryptocurrency found for {query!r}")
        match = matches[0]
        register_coin(match["symbol"], match["id"])
        return cls(match["pair"])

    @staticmethod
    def search(query: str, quote: str = "USD", limit: int = 10) -> list:
        """Find coins and return names, symbols, IDs, ranks, and usable pairs."""
        return search_symbol(query, quote=quote, limit=limit)

    # ── Internals ─────────────────────────────────────────────────────────

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def coingecko_id(self) -> str:
        """CoinGecko ID currently mapped to this asset."""
        return resolve_cg_id(self._symbol.split("_")[0].upper())

    # ── Price & OHLCV ─────────────────────────────────────────────────────

    @property
    def price(self) -> float:
        """Current spot price."""
        return get_price(self._symbol)

    def history(self, days: int = 30, interval: str = "daily") -> pd.DataFrame:
        """OHLCV history.

        Parameters
        ----------
        days     : lookback (default 30)
        interval : ``'daily'``, ``'hourly'``, ``'4h'``, ``'15m'``, ``'5m'``, ``'1m'``
        """
        return get_history(self._symbol, days=days, interval=interval)

    @property
    def fast_info(self) -> dict:
        """Quick snapshot — price, market cap, 24h change.

        Derived from the cached coin profile, using its ten-minute expiry.
        """
        def _build():
            info = get_info(self._symbol)
            return {
                "symbol": self._symbol.upper(),
                "price": info.get("current_price"),
                "market_cap": info.get("market_cap"),
                "volume_24h": info.get("total_volume_24h"),
                "change_24h_pct": info.get("price_change_pct_24h"),
                "change_7d_pct": info.get("price_change_pct_7d"),
                "rank": info.get("rank"),
                "ath": info.get("ath"),
                "ath_change_pct": info.get("ath_change_pct"),
            }
        return _build()

    # ── Fundamental ───────────────────────────────────────────────────────

    @property
    def info(self) -> dict:
        """Full coin profile: description, links, ATH, social stats, dev activity."""
        return get_info(self._symbol)

    @property
    def market_cap(self) -> pd.DataFrame:
        """Historical market cap (30 days by default)."""
        return get_market_cap(self._symbol)

    @property
    def volume(self) -> pd.DataFrame:
        """Historical trading volume (30 days by default)."""
        return get_volume(self._symbol)

    @property
    def dominance(self) -> Optional[float]:
        """This asset's share of the total crypto market cap (%)."""
        d = get_dominance()
        base = self._symbol.split("_")[0].upper()
        return d.get(base)

    # ── Derivatives ───────────────────────────────────────────────────────

    @property
    def funding_rate(self) -> pd.DataFrame:
        """Historical 8-hour funding rates for the perpetual futures contract.

        Requires an active Binance USDT-margined perp for this asset.
        """
        return get_funding_rate(self._symbol)

    @property
    def open_interest(self) -> pd.DataFrame:
        """Historical open interest for the perpetual futures contract."""
        return get_open_interest(self._symbol)

    @property
    def long_short_ratio(self) -> pd.DataFrame:
        """Global long/short account ratio from Binance Futures."""
        return get_long_short_ratio(self._symbol)

    # ── On-chain ──────────────────────────────────────────────────────────

    @property
    def onchain(self) -> pd.DataFrame:
        """On-chain metrics: active addresses, tx count, NVT, hash rate, etc.

        Data from the CoinMetrics Community API (free tier).
        Not available for every asset — see ``get_onchain()`` docs.
        """
        base = self._symbol.split("_")[0]
        return get_onchain(base)

    # ── Sentiment ─────────────────────────────────────────────────────────

    @property
    def news(self) -> list:
        """Recent matching headlines from public CoinDesk/Cointelegraph RSS feeds."""
        return get_news(self._symbol)

    # ── Technical Analysis ────────────────────────────────────────────────

    def technicals(self, days: int = 90) -> pd.DataFrame:
        """OHLCV + RSI, MACD, Bollinger Bands, EMA, ATR, OBV.

        Requires ``pip install 'crypto-yfinance[ta]'``.
        """
        return get_technicals(self._symbol, days=days)

    # ── Plotting ──────────────────────────────────────────────────────────

    def plot(self, days: int = 30, interval: str = "daily",
             show_volume: bool = True, show_rsi: bool = True,
             moving_averages=(20, 50), show_bollinger: bool = False,
             theme: str = "plotly_dark", show: bool = True):
        """Return an interactive candlestick chart with optional indicators."""
        return plot_price(self._symbol, days=days, interval=interval,
                          show_volume=show_volume, show_rsi=show_rsi,
                          moving_averages=moving_averages,
                          show_bollinger=show_bollinger,
                          theme=theme, show=show)

    # ── Dunder ────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"Ticker('{self._symbol}')"

    def __str__(self) -> str:
        try:
            p = get_price(self._symbol)
            return f"{self._symbol.upper()}  |  ${p:,.4f}"
        except Exception:
            return f"Ticker('{self._symbol}')"
