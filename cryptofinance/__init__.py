"""
crypto-yfinance
~~~~~~~~~~~~~~~
Unified cryptocurrency data — prices, history, on-chain metrics, derivatives,
DeFi TVL, sentiment, and more. All in one library, all with one import.

    >>> from cryptofinance import Ticker, download
    >>> t = Ticker('BTC_USD')
    >>> t.history(days=90)
    >>> t.onchain
    >>> t.plot()

    >>> from cryptofinance import get_fear_greed, plot_dominance
    >>> get_fear_greed(30)
    >>> plot_dominance()
"""

__version__ = "0.2.1"
__author__  = "Aakash Chavan Ravindranath"

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

# ── OOP interface ────────────────────────────────────────────────────────────
from .ticker  import Ticker
from .tickers import Tickers, download

# ── Market data ──────────────────────────────────────────────────────────────
from .utils.get_price      import get_price
from .utils.get_history    import get_history
from .utils.get_market_cap import get_market_cap
from .utils.get_volume     import get_volume
from .utils.get_info       import get_info
from .utils.get_trending   import get_trending
from .utils.get_top_coins  import get_top_coins
from .utils.get_global     import get_global
from .utils.get_dominance  import get_dominance
from .utils.get_news       import get_news
from .utils.search_symbol  import search_symbol

# ── Sentiment ────────────────────────────────────────────────────────────────
from .utils.get_fear_greed import get_fear_greed

# ── Derivatives (Binance Futures) ────────────────────────────────────────────
from .utils.get_funding_rate  import get_funding_rate
from .utils.get_open_interest import get_open_interest
from .utils.get_long_short    import get_long_short_ratio

# ── On-chain (CoinMetrics Community) ─────────────────────────────────────────
from .utils.get_onchain import get_onchain

# ── DeFi (DeFiLlama) ─────────────────────────────────────────────────────────
from .utils.get_defi_tvl import get_defi_tvl, get_top_defi, get_tvl_by_chain

# ── Gas ──────────────────────────────────────────────────────────────────────
from .utils.get_gas import get_gas

# ── Technical analysis ────────────────────────────────────────────────────────
from .utils.get_technicals import get_technicals

# ── Plots ─────────────────────────────────────────────────────────────────────
from .utils.plot_price import plot_price
from .utils.plots import (
    plot_fear_greed,
    plot_dominance,
    plot_market_cap,
    plot_compare,
    plot_correlation,
    plot_funding_rate,
    plot_onchain,
    plot_defi_tvl,
    plot_market_snapshot,
)

# ── Cache control ─────────────────────────────────────────────────────────────
from .utils.cache import clear_cache

__all__ = [
    # OOP
    "Ticker", "Tickers", "download",
    # Market data
    "get_price", "get_history", "get_market_cap", "get_volume",
    "get_info", "get_trending", "get_top_coins", "get_global",
    "get_dominance", "get_news", "search_symbol",
    # Sentiment
    "get_fear_greed",
    # Derivatives
    "get_funding_rate", "get_open_interest", "get_long_short_ratio",
    # On-chain
    "get_onchain",
    # DeFi
    "get_defi_tvl", "get_top_defi", "get_tvl_by_chain",
    # Gas
    "get_gas",
    # Technical analysis
    "get_technicals",
    # Plots
    "plot_price", "plot_fear_greed", "plot_dominance", "plot_market_cap",
    "plot_compare", "plot_correlation", "plot_funding_rate",
    "plot_onchain", "plot_defi_tvl", "plot_market_snapshot",
    # Utilities
    "clear_cache",
]
