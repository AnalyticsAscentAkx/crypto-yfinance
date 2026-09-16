# cryptofinance/utils/get_price.py
from .clients import CoinGeckoAPI
import ccxt
import logging
from .cache import ttl_cache
from .validation import split_pair

logger = logging.getLogger("cryptofinance")
from .coingecko_resolver import resolve_cg_id

def _ccxt_try(exchange, symbols):
    try:
        exchange.timeout = 15000
        exchange.enableRateLimit = True
        exchange.load_markets()
        for s in symbols:
            if s in exchange.markets:
                return exchange.fetch_ticker(s)['last']
    except Exception as exc:
        logger.debug("Price provider failed: %s", exc)
    return None

@ttl_cache(ttl=300)
def get_price(symbol: str) -> float:
    base, quote = (p.lower() for p in split_pair(symbol))
    bU, qU = base.upper(), quote.upper()

    # Coingecko first
    try:
        cg = CoinGeckoAPI()
        cg_id = resolve_cg_id(bU)
        data = cg.get_price(ids=cg_id, vs_currencies=quote)
        val = data.get(cg_id, {}).get(quote)
        if val is not None:
            return float(val)
    except Exception as exc:
        logger.debug("Price provider failed: %s", exc)

    # CCXT fallbacks
    binance_symbols = [f"{bU}/USDT"] if qU == "USD" else [f"{bU}/{qU}"]
    coinbase_symbols = [f"{bU}/{qU}"]
    kr_base = bU  # CCXT uses normalized BTC symbols for Kraken
    kraken_symbols = [f"{kr_base}/{qU}"]

    for ex, syms in (ccxt.binance(), binance_symbols), (ccxt.coinbase(), coinbase_symbols), (ccxt.kraken(), kraken_symbols):
        px = _ccxt_try(ex, syms)
        if px is not None:
            return float(px)

    raise ValueError(f"Price fetch failed for {symbol}: no market across Coingecko/Binance/Coinbase/Kraken")