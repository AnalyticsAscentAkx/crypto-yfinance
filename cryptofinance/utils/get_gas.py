import requests
from .cache import ttl_cache


@ttl_cache(ttl=60)
def get_gas() -> dict:
    """Return current Ethereum gas prices in Gwei.

    Tries multiple free sources with automatic fallback.

    Returns
    -------
    dict with keys: slow, standard, fast, rapid (all in Gwei), and source

    Example
    -------
    >>> gas = get_gas()
    >>> print(f"Fast: {gas['fast']} Gwei")
    """
    # Primary: beaconcha.in (free, no key)
    try:
        resp = requests.get("https://beaconcha.in/api/v1/execution/gasnow", timeout=8)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        if data:
            return {
                "slow":     round(data.get("slow", 0) / 1e9, 2),
                "standard": round(data.get("standard", 0) / 1e9, 2),
                "fast":     round(data.get("fast", 0) / 1e9, 2),
                "rapid":    round(data.get("rapid", 0) / 1e9, 2),
                "unit":     "gwei",
                "source":   "beaconcha.in",
            }
    except Exception:
        pass

    # Fallback: ethgasstation.info
    try:
        resp = requests.get("https://ethgasstation.info/api/ethgasAPI.json", timeout=8)
        resp.raise_for_status()
        data = resp.json()
        return {
            "slow":     round(data.get("safeLow", 0) / 10, 2),
            "standard": round(data.get("average", 0) / 10, 2),
            "fast":     round(data.get("fast", 0) / 10, 2),
            "rapid":    round(data.get("fastest", 0) / 10, 2),
            "unit":     "gwei",
            "source":   "ethgasstation",
        }
    except Exception:
        pass

    raise ValueError(
        "Could not fetch gas prices. Both beaconcha.in and ethgasstation.info are unreachable."
    )
