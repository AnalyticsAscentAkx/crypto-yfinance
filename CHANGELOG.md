# Changelog

## 0.2.1 — 2026-09-16

### Fixed

- Treat `days` as calendar days for every OHLCV interval. Intraday history now paginates and returns a complete window of closed candles.
- Preserve full pair names in multi-asset downloads. Columns now match the documented `(field, symbol)` layout, including pairs such as `BTC_USD` and `BTC_EUR` together.
- Restore Python 3.9 compatibility by avoiding runtime evaluation of Python 3.10-only union syntax.
- Query only Coin Metrics metrics currently available to Community users; unavailable output columns remain `NaN` and are named in `DataFrame.attrs`.
- Use Binance's documented `fapi.binance.com` base for open interest and long/short data.
- Resample CoinGecko fallback candles to the requested interval when lossless aggregation is possible; reject unsupported coarse fallbacks.
- Make cached mutable values safe to edit, bound the cache size, cache current prices, and make `clear_cache()` refresh existing `Ticker` objects.
- Avoid RSI chart crashes when history is too short, and return the Plotly figure for embedding or export.
- Replace the retired Messari news endpoint with filtered public CoinDesk and Cointelegraph RSS headlines.
- Correct the package's GitHub source and issue links.
- Handle DeFiLlama protocols whose current TVL is null without failing the ranking.

### Added

- Input validation for symbols, intervals, periods, limits, and lookback days.
- Bounded interval-specific history lookbacks to protect public provider rate limits.
- Shared bounded retries and connection reuse for the repaired direct HTTP integrations, plus opt-in `cryptofinance` diagnostic logging.
- Provider and candle metadata in `DataFrame.attrs`.
- Deterministic regression tests and GitHub Actions checks for Python 3.9–3.13.
- Optional `COINGECKO_DEMO_API_KEY`; the package still works without an API key.

### Changed

- The `ta` and `full` extras use `pandas-ta-classic`, which supports the package's advertised Python versions.
- History timestamps consistently represent timezone-naive UTC candle opens and exclude incomplete candles.
- CoinGecko fallback volume is `NaN` because its market-chart volume is not exchange candle volume.
