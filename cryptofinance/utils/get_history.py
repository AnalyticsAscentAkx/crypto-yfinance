"""Complete, closed OHLCV candles with consistent intervals across providers."""
import logging
import time

import ccxt
import pandas as pd

from .clients import CoinGeckoAPI
from .coingecko_resolver import resolve_cg_id
from .cache import ttl_cache
from .validation import positive_int, split_pair

logger = logging.getLogger('cryptofinance')
_TF_MAP = {'daily': '1d', 'hourly': '1h', '4h': '4h', '15m': '15m', '5m': '5m', '1m': '1m'}
_STEP_MS = {'daily': 86400000, 'hourly': 3600000, '4h': 14400000,
            '15m': 900000, '5m': 300000, '1m': 60000}
_MAX_DAYS = {'daily': 3650, 'hourly': 365, '4h': 730,
             '15m': 90, '5m': 30, '1m': 7}
_COLUMNS = ['timestamp', 'open', 'high', 'low', 'close', 'volume']


def _now_ms():
    return int(time.time() * 1000)


def _validate_window(df, start, end, step):
    df = df.drop_duplicates('timestamp').sort_values('timestamp')
    df = df[(df.timestamp >= pd.to_datetime(start, unit='ms')) &
            (df.timestamp < pd.to_datetime(end, unit='ms'))].reset_index(drop=True)
    expected = (end - start) // step
    if (len(df) != expected or df.empty or
            df.timestamp.iloc[0] != pd.to_datetime(start, unit='ms') or
            not (df.timestamp.diff().dropna() == pd.Timedelta(milliseconds=step)).all()):
        raise ValueError(f'Incomplete history: expected {expected} consecutive closed candles, got {len(df)}')
    if df[['open', 'high', 'low', 'close']].isna().any().any():
        raise ValueError('Provider returned missing OHLC prices')
    return df


def _exchange_ohlcv(exchange_cls, base, quote, interval, start, end):
    ex = exchange_cls()
    ex.timeout = 15000
    ex.enableRateLimit = True
    name = getattr(ex, 'id', exchange_cls.__name__)
    actual_quote = 'USDT' if quote == 'USD' and name in ('binance', 'okx') else quote
    pair = f'{base}/{actual_quote}'
    step = _STEP_MS[interval]
    cursor, rows = start, []
    # Coinbase allows 300 candles per request; the other providers accept at least this.
    page_limit = 300 if name == 'coinbase' else 1000
    while cursor < end:
        limit = min(page_limit, (end - cursor) // step)
        page = ex.fetch_ohlcv(pair, timeframe=_TF_MAP[interval], since=cursor, limit=limit)
        if not page:
            break
        rows.extend(page)
        next_cursor = max(row[0] for row in page) + step
        if next_cursor <= cursor:
            break
        cursor = next_cursor
    df = pd.DataFrame(rows, columns=_COLUMNS)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = _validate_window(df, start, end, step)
    df.attrs.update(source=name, requested_symbol=f'{base}_{quote}',
                    actual_symbol=f'{base}_{actual_quote}', interval=interval,
                    volume_unit=base, timestamp_convention='UTC candle open; timezone-naive',
                    closed_candles_only=True)
    return df


def _coingecko_ohlcv(base, quote, days, interval, start, end):
    cg = CoinGeckoAPI()
    cg_id = resolve_cg_id(base)
    # Request extra history so the first resampled bucket can be complete.
    lookback = days + 1
    supported = [1, 7, 14, 30, 90, 180, 365]
    candidates = [d for d in supported if d >= lookback]
    if not candidates:
        raise ValueError('CoinGecko Demo cannot supply this history window')
    provider_days = min(candidates)
    source_step = (1800000 if provider_days <= 2 else
                   14400000 if provider_days <= 30 else 345600000)
    step = _STEP_MS[interval]
    if source_step > step or step % source_step:
        raise ValueError('CoinGecko Demo candles are too coarse for the requested interval')
    rows = cg.get_coin_ohlc_by_id(id=cg_id, vs_currency=quote.lower(), days=provider_days)
    df = pd.DataFrame(rows, columns=_COLUMNS[:-1])
    if df.empty:
        raise ValueError('CoinGecko returned no OHLC candles')
    # CoinGecko labels candle CLOSE time; exchange results label candle OPEN time.
    df['timestamp'] = pd.to_datetime(df.timestamp - source_step, unit='ms')
    df = df.drop_duplicates('timestamp').sort_values('timestamp').set_index('timestamp')
    rule = pd.Timedelta(milliseconds=step)
    grouped = df.resample(rule, origin='epoch', closed='left', label='left')
    result = grouped.agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'})
    # Never pass partial aggregation buckets off as complete candles.
    result = result[grouped['close'].count() == step // source_step].reset_index()
    # CoinGecko's market-chart volume is a rolling 24h quote-currency amount,
    # not exchange candle volume. Preserve the column but do not substitute it.
    result['volume'] = float('nan')
    result = _validate_window(result, start, end, step)
    result.attrs.update(source='coingecko', requested_symbol=f'{base}_{quote}',
                        actual_symbol=f'{base}_{quote}', interval=interval,
                        volume_unit=None, volume_available=False,
                        timestamp_convention='UTC candle open; timezone-naive', closed_candles_only=True)
    return result


@ttl_cache(ttl=300)
def get_history(symbol: str, days: int = 30, interval: str = 'daily') -> pd.DataFrame:
    """Return a complete window of closed OHLCV candles ending at the last boundary.

    ``days`` always means calendar days, including for intraday intervals. The
    currently forming candle is excluded. Timestamps are timezone-naive UTC candle
    opens. Provider/quote information is in ``DataFrame.attrs``. A provider unable
    to supply the requested window is skipped; if none can, ValueError is raised.
    """
    base, quote = split_pair(symbol)
    if interval not in _TF_MAP:
        raise ValueError(f'interval must be one of {list(_TF_MAP)}')
    positive_int(days, 'days', _MAX_DAYS[interval])
    step = _STEP_MS[interval]
    end = (_now_ms() // step) * step
    start = end - days * 86400000
    errors = []
    for exchange_cls in (ccxt.binance, ccxt.coinbase, ccxt.kraken, ccxt.okx):
        try:
            result = _exchange_ohlcv(exchange_cls, base, quote, interval, start, end)
            result.attrs['fetched_at'] = pd.Timestamp.now(tz='UTC').isoformat()
            logger.debug('history symbol=%s source=%s rows=%s', symbol, result.attrs['source'], len(result))
            return result
        except Exception as exc:
            errors.append((exchange_cls.__name__, exc))
            logger.debug('history provider=%s symbol=%s failed: %s', exchange_cls.__name__, symbol, exc)
    try:
        result = _coingecko_ohlcv(base, quote, days, interval, start, end)
        result.attrs['fetched_at'] = pd.Timestamp.now(tz='UTC').isoformat()
        return result
    except Exception as exc:
        errors.append(('coingecko', exc))
    reasons = '; '.join(f'{name}: {exc}' for name, exc in errors)
    raise ValueError(f'Could not fetch complete {interval} history for {symbol}. {reasons}') from errors[-1][1]
