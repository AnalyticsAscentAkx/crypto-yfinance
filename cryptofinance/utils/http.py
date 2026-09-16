"""Shared public-data HTTP transport, with bounded retries and opt-in logs."""
import logging
import threading
import time
from urllib.parse import urlsplit

import requests

logger = logging.getLogger("cryptofinance")
_LOCAL = threading.local()
_RETRYABLE = {429, 500, 502, 503, 504}


def _session():
    if not hasattr(_LOCAL, "session"):
        _LOCAL.session = requests.Session()
        _LOCAL.session.headers["User-Agent"] = "crypto-yfinance/0.3.0"
    return _LOCAL.session


def get_response(url, params=None, timeout=15):
    target = urlsplit(url)
    label = target.netloc + target.path
    for attempt in range(3):
        started = time.monotonic()
        try:
            response = _session().get(url, params=params, timeout=(5, timeout))
        except (requests.ConnectionError, requests.Timeout):
            if attempt == 2:
                logger.warning("GET %s failed after 3 attempts", label)
                raise
            logger.debug("GET %s retry=%s after connection/timeout error", label, attempt + 1)
            time.sleep(0.5 * (2 ** attempt))
            continue
        logger.debug("GET %s status=%s attempt=%s elapsed=%.3fs", label,
                     response.status_code, attempt + 1, time.monotonic() - started)
        if response.status_code in _RETRYABLE and attempt < 2:
            try:
                delay = float(response.headers.get("Retry-After", 0.5 * (2 ** attempt)))
            except ValueError:
                delay = 0.5 * (2 ** attempt)
            response.close()
            time.sleep(min(5, max(0, delay)))
            continue
        response.raise_for_status()
        return response


def get_json(url, params=None, timeout=15):
    response = get_response(url, params=params, timeout=timeout)
    try:
        data = response.json()
    except ValueError as exc:
        raise ValueError(f"{urlsplit(url).netloc} returned invalid or empty JSON "
                         f"(HTTP {response.status_code})") from exc
    if not isinstance(data, (dict, list)):
        raise ValueError(f"{urlsplit(url).netloc} returned an unexpected JSON value")
    return data
