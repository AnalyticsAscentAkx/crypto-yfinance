from .clients import CoinGeckoAPI
from .cache import ttl_cache


@ttl_cache(ttl=300)
def get_global() -> dict:
    """Return a snapshot of the overall crypto market.

    Returns
    -------
    dict with keys:
        active_cryptocurrencies, total_market_cap_usd, total_volume_24h_usd,
        btc_dominance, eth_dominance, market_cap_change_pct_24h,
        defi_volume_24h_usd, defi_market_cap_usd, stablecoin_volume_24h_usd,
        stablecoin_market_cap_usd, derivatives_volume_24h_usd, markets
    """
    cg = CoinGeckoAPI()
    raw = cg.get_global()

    return {
        "active_cryptocurrencies": raw.get("active_cryptocurrencies"),
        "markets": raw.get("markets"),
        "total_market_cap_usd": raw.get("total_market_cap", {}).get("usd"),
        "total_volume_24h_usd": raw.get("total_volume", {}).get("usd"),
        "btc_dominance": raw.get("market_cap_percentage", {}).get("btc"),
        "eth_dominance": raw.get("market_cap_percentage", {}).get("eth"),
        "market_cap_change_pct_24h": raw.get("market_cap_change_percentage_24h_usd"),
        "defi_volume_24h_usd": raw.get("total_defi_volume_usd"),
        "defi_market_cap_usd": raw.get("total_defi_market_cap_usd"),
        "stablecoin_volume_24h_usd": raw.get("total_volume_usd"),
        "stablecoin_market_cap_usd": raw.get("total_market_cap_usd"),
        "derivatives_volume_24h_usd": raw.get("total_value_locked_usd"),
        "ongoing_icos": raw.get("ongoing_icos"),
        "ended_icos": raw.get("ended_icos"),
        "upcoming_icos": raw.get("upcoming_icos"),
    }
