from typing import Optional

from .clients import CoinGeckoAPI

# Pre-built map for the top ~100 coins by market cap.
# Saves an API round-trip for the most common assets.
CG_ID_MAP = {
    # Top 10
    "BTC":   "bitcoin",
    "ETH":   "ethereum",
    "USDT":  "tether",
    "BNB":   "binancecoin",
    "SOL":   "solana",
    "XRP":   "ripple",
    "USDC":  "usd-coin",
    "ADA":   "cardano",
    "AVAX":  "avalanche-2",
    "DOGE":  "dogecoin",
    # 11–30
    "TRX":   "tron",
    "TON":   "the-open-network",
    "LINK":  "chainlink",
    "DOT":   "polkadot",
    "MATIC": "matic-network",
    "SHIB":  "shiba-inu",
    "LTC":   "litecoin",
    "UNI":   "uniswap",
    "ATOM":  "cosmos",
    "XLM":   "stellar",
    "BCH":   "bitcoin-cash",
    "ETC":   "ethereum-classic",
    "NEAR":  "near",
    "APT":   "aptos",
    "ICP":   "internet-computer",
    "FIL":   "filecoin",
    "HBAR":  "hedera-hashgraph",
    "ARB":   "arbitrum",
    "VET":   "vechain",
    "OP":    "optimism",
    # 31–60
    "AAVE":  "aave",
    "MKR":   "maker",
    "GRT":   "the-graph",
    "SNX":   "synthetix-network-token",
    "CRV":   "curve-dao-token",
    "COMP":  "compound-governance-token",
    "LDO":   "lido-dao",
    "FTM":   "fantom",
    "ALGO":  "algorand",
    "MANA":  "decentraland",
    "SAND":  "the-sandbox",
    "AXS":   "axie-infinity",
    "XMR":   "monero",
    "EOS":   "eos",
    "THETA": "theta-token",
    "XTZ":   "tezos",
    "EGLD":  "elrond-erd-2",
    "FLOW":  "flow",
    "KSM":   "kusama",
    "ZEC":   "zcash",
    "DASH":  "dash",
    "NEO":   "neo",
    "WAVES": "waves",
    "ENJ":   "enjincoin",
    "BAT":   "basic-attention-token",
    "ZIL":   "zilliqa",
    "IOTA":  "iota",
    "BTT":   "bittorrent",
    "ONE":   "harmony",
    # 61–80
    "CAKE":  "pancakeswap-token",
    "1INCH": "1inch",
    "CHZ":   "chiliz",
    "ROSE":  "oasis-network",
    "QNT":   "quant-network",
    "STX":   "blockstack",
    "RUNE":  "thorchain",
    "INJ":   "injective-protocol",
    "SUI":   "sui",
    "SEI":   "sei-network",
    "TIA":   "celestia",
    "WIF":   "dogwifcoin",
    "PEPE":  "pepe",
    "FLOKI": "floki",
    "BONK":  "bonk",
    "JTO":   "jito-governance-token",
    "PYTH":  "pyth-network",
    "JUP":   "jupiter-exchange-solana",
    "WLD":   "worldcoin-wld",
    "BLUR":  "blur",
    # 81–100
    "GMX":   "gmx",
    "DYDX":  "dydx",
    "IMX":   "immutable-x",
    "RNDR":  "render-token",
    "FET":   "fetch-ai",
    "AGIX":  "singularitynet",
    "OCEAN": "ocean-protocol",
    "GALA":  "gala",
    "ENS":   "ethereum-name-service",
    "LRC":   "loopring",
    "ZRX":   "0x",
    "SUSHI": "sushi",
    "YFI":   "yearn-finance",
    "UMA":   "uma",
    "BAL":   "balancer",
    "ANKR":  "ankr",
    "SKL":   "skale",
    "CELR":  "celer-network",
    "BAND":  "band-protocol",
    "REN":   "republic-protocol",
    # Newer and fast-moving assets. Unknown symbols are also resolved live.
    "POL":   "polygon-ecosystem-token",
    "KAS":   "kaspa",
    "TAO":   "bittensor",
    "HYPE":  "hyperliquid",
    "ONDO":  "ondo-finance",
    "TRUMP": "official-trump",
    "ENA":   "ethena",
    "AERO":  "aerodrome-finance",
    "PENGU": "pudgy-penguins",
    "W":     "wormhole",
    "JASMY": "jasmycoin",
    "RENDER":"render-token",
}


def register_coin(symbol: str, coin_id: str) -> None:
    """Register or override a CoinGecko symbol mapping for this process.

    This is useful for newly launched assets and symbols shared by multiple
    projects. ``Ticker.from_name()`` calls it automatically.
    """
    clean_symbol = str(symbol).strip().upper()
    clean_id = str(coin_id).strip().lower()
    if not clean_symbol or not clean_id:
        raise ValueError("symbol and coin_id must be non-empty")
    CG_ID_MAP[clean_symbol] = clean_id


def _rank(coin: dict) -> int:
    value = coin.get("market_cap_rank")
    return value if isinstance(value, int) and value > 0 else 10**9


def resolve_coin(query: str) -> Optional[dict]:
    """Return the best CoinGecko search result for a symbol, name, or ID."""
    clean = str(query).strip()
    if not clean:
        return None
    response = CoinGeckoAPI().search(clean)
    coins = response.get("coins", [])
    lowered = clean.lower()
    exact = [
        coin for coin in coins
        if coin.get("id", "").lower() == lowered
        or coin.get("symbol", "").lower() == lowered
        or coin.get("name", "").lower() == lowered
    ]
    candidates = exact or coins
    if not candidates:
        return None
    return min(candidates, key=_rank)


def resolve_cg_id(symbol_upper: str) -> str:
    """Return the CoinGecko asset ID for a given ticker symbol.

    Tries the local map first; falls back to a live CoinGecko search if not found.
    Successful lookups are cached in-process so you only pay the API cost once.
    """
    if symbol_upper in CG_ID_MAP:
        return CG_ID_MAP[symbol_upper]
    try:
        coin = resolve_coin(symbol_upper)
        if coin and coin.get("id"):
            cg_id = coin["id"]
            register_coin(symbol_upper, cg_id)
            return cg_id
    except Exception:
        pass
    return symbol_upper.lower()
