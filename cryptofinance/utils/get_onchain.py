"""Coin Metrics data restricted to metrics available in the Community catalog."""
import datetime
import logging
import re

import pandas as pd
import requests

from .cache import ttl_cache
from .http import get_json
from .validation import asset_symbol, positive_int

logger = logging.getLogger('cryptofinance')
_CM_BASE = 'https://community-api.coinmetrics.io/v4'
_METRICS = {
    'AdrActCnt': 'active_addresses', 'TxCnt': 'tx_count',
    'TxTfrValAdjUSD': 'transfer_volume_usd', 'NVTAdj': 'nvt_ratio',
    'HashRate': 'hash_rate', 'FeeMeanNtv': 'mean_fee_native', 'BlkCnt': 'block_count',
}


def _pages(path, params):
    params = dict(params)
    seen = set()
    while True:
        result = get_json(f'{_CM_BASE}/{path}', params=params)
        if not isinstance(result, dict) or not isinstance(result.get('data'), list):
            raise ValueError('Coin Metrics returned an unexpected response')
        yield from result['data']
        token = result.get('next_page_token')
        if not token:
            break
        if token in seen:
            raise ValueError('Coin Metrics returned a repeated pagination token')
        seen.add(token)
        params['next_page_token'] = token


@ttl_cache(ttl=3600)
def _available_metrics(asset):
    available = set()
    for entry in _pages('catalog-v2/asset-metrics', {
            'assets': asset, 'metrics': ','.join(_METRICS), 'page_size': 100}):
        if entry.get('asset') != asset:
            continue
        for metric in entry.get('metrics', []):
            if any(f.get('frequency') == '1d' and f.get('community') is True
                   for f in metric.get('frequencies', [])):
                available.add(metric['metric'])
    return [m for m in _METRICS if m in available]


@ttl_cache(ttl=3600)
def get_onchain(symbol: str, days: int = 90) -> pd.DataFrame:
    """Return available daily Community metrics; inaccessible columns contain NaN.

    ``DataFrame.attrs['unavailable_metrics']`` names the unavailable output columns.
    No paid metric is substituted or estimated. Data publication may lag by a day.
    """
    asset = asset_symbol(symbol).lower()
    positive_int(days, 'days')
    today = datetime.datetime.now(datetime.timezone.utc).date()
    metrics = _available_metrics(asset)
    entries = []
    while metrics:
        try:
            entries = list(_pages('timeseries/asset-metrics', {
                'assets': asset, 'metrics': ','.join(metrics),
                'start_time': (today - datetime.timedelta(days=days)).isoformat(),
                'end_time': today.isoformat(), 'end_inclusive': 'false',
                'frequency': '1d', 'page_size': min(days, 10000),
            }))
            break
        except requests.HTTPError as exc:
            # Catalog permissions can change between the catalog and data requests.
            if exc.response is None or exc.response.status_code != 403:
                raise
            match = re.search(r"Requested metric '([^']+)'", exc.response.text)
            if not match or match.group(1) not in metrics:
                raise
            denied = match.group(1)
            logger.warning('Coin Metrics revoked community access to %s for %s', denied, asset)
            metrics.remove(denied)
    if not metrics:
        raise ValueError(f"No requested on-chain metrics are available for '{symbol}' in the Community tier")
    if not entries:
        raise ValueError(f"No on-chain data returned for '{symbol}' in the requested window")
    rows = [{'timestamp': pd.to_datetime(entry['time'], utc=True),
             **{column: _safe_float(entry.get(metric)) for metric, column in _METRICS.items()}}
            for entry in entries]
    df = pd.DataFrame(rows).drop_duplicates('timestamp').sort_values('timestamp').reset_index(drop=True)
    unavailable = [column for metric, column in _METRICS.items() if metric not in metrics]
    df.attrs.update(source='coinmetrics-community', unavailable_metrics=unavailable,
                    fetched_at=pd.Timestamp.now(tz='UTC').isoformat())
    if unavailable:
        logger.debug('On-chain symbol=%s unavailable_metrics=%s', symbol, unavailable)
    return df


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float('nan')
