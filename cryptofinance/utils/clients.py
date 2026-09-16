"""Reusable CoinGecko clients with a timeout and optional Demo API key."""
import os
import threading
from pycoingecko import CoinGeckoAPI as _CoinGeckoAPI

_LOCAL = threading.local()


def CoinGeckoAPI():
    key = os.getenv("COINGECKO_DEMO_API_KEY", "")
    if getattr(_LOCAL, "key", None) != key or not hasattr(_LOCAL, "client"):
        _LOCAL.client = _CoinGeckoAPI(retries=2, demo_api_key=key)
        _LOCAL.client.request_timeout = 15
        _LOCAL.key = key
    return _LOCAL.client
