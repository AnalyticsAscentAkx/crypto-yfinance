from .clients import CoinGeckoAPI
from .coingecko_resolver import resolve_cg_id
from .cache import ttl_cache


@ttl_cache(ttl=600)
def get_info(symbol: str) -> dict:
    """Return a rich profile for a coin — similar to ``yfinance``'s ``.info``.

    Parameters
    ----------
    symbol : e.g. ``'BTC_USD'`` or just ``'BTC'``

    Returns
    -------
    dict with keys: name, symbol, rank, description, homepage, whitepaper,
    twitter, reddit, github, genesis_date, hashing_algorithm,
    current_price, market_cap, market_cap_rank, ath, ath_date, atl, atl_date,
    price_change_24h, price_change_pct_24h, circulating_supply, total_supply,
    max_supply, twitter_followers, reddit_subscribers, coingecko_score,
    developer_score, community_score, liquidity_score, public_interest_score
    """
    base = symbol.lower().split("_")[0]
    cg = CoinGeckoAPI()
    cg_id = resolve_cg_id(base.upper())

    raw = cg.get_coin_by_id(
        id=cg_id,
        localization=False,
        tickers=False,
        market_data=True,
        community_data=True,
        developer_data=True,
        sparkline=False,
    )

    md = raw.get("market_data", {})
    links = raw.get("links", {})
    community = raw.get("community_data", {})
    dev = raw.get("developer_data", {})

    def _first(lst):
        return lst[0] if lst else None

    return {
        # Identity
        "name": raw.get("name"),
        "symbol": raw.get("symbol", "").upper(),
        "coingecko_id": cg_id,
        "rank": raw.get("market_cap_rank"),
        "genesis_date": raw.get("genesis_date"),
        "hashing_algorithm": raw.get("hashing_algorithm"),
        "description": raw.get("description", {}).get("en", ""),
        # Links
        "homepage": _first(links.get("homepage", [])),
        "whitepaper": _first(links.get("whitepaper", [])) or _first(links.get("announcement_url", [])),
        "twitter": links.get("twitter_screen_name"),
        "reddit": links.get("subreddit_url"),
        "github": _first(links.get("repos_url", {}).get("github", [])),
        # Price & market
        "current_price": md.get("current_price", {}).get("usd"),
        "market_cap": md.get("market_cap", {}).get("usd"),
        "market_cap_rank": md.get("market_cap_rank"),
        "fully_diluted_valuation": md.get("fully_diluted_valuation", {}).get("usd"),
        "total_volume_24h": md.get("total_volume", {}).get("usd"),
        "price_change_24h": md.get("price_change_24h"),
        "price_change_pct_24h": md.get("price_change_percentage_24h"),
        "price_change_pct_7d": md.get("price_change_percentage_7d"),
        "price_change_pct_30d": md.get("price_change_percentage_30d"),
        "price_change_pct_1y": md.get("price_change_percentage_1y"),
        # Supply
        "circulating_supply": md.get("circulating_supply"),
        "total_supply": md.get("total_supply"),
        "max_supply": md.get("max_supply"),
        # ATH / ATL
        "ath": md.get("ath", {}).get("usd"),
        "ath_date": md.get("ath_date", {}).get("usd"),
        "ath_change_pct": md.get("ath_change_percentage", {}).get("usd"),
        "atl": md.get("atl", {}).get("usd"),
        "atl_date": md.get("atl_date", {}).get("usd"),
        "atl_change_pct": md.get("atl_change_percentage", {}).get("usd"),
        # Community
        "twitter_followers": community.get("twitter_followers"),
        "reddit_subscribers": community.get("reddit_subscribers"),
        "reddit_active_48h": community.get("reddit_accounts_active_48h"),
        "telegram_users": community.get("telegram_channel_user_count"),
        # Developer activity
        "github_stars": dev.get("stars"),
        "github_forks": dev.get("forks"),
        "github_subscribers": dev.get("subscribers"),
        "github_total_issues": dev.get("total_issues"),
        "github_closed_issues": dev.get("closed_issues"),
        "github_prs_merged": dev.get("pull_requests_merged"),
        "commit_count_4w": dev.get("commit_count_4_weeks"),
        # CoinGecko scores
        "coingecko_score": raw.get("coingecko_score"),
        "developer_score": raw.get("developer_score"),
        "community_score": raw.get("community_score"),
        "liquidity_score": raw.get("liquidity_score"),
        "public_interest_score": raw.get("public_interest_score"),
    }
