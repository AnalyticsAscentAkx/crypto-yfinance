# Changelog

## 0.3.1 (2026-10-20)

### Fixed

- `get_funding_rate()` annualized every contract as if it settled every 8 hours.
  Many Binance perps settle every 4 hours or hourly, so their `annualized_pct` was
  2 to 8 times too low. The interval is now measured per row and returned as
  `funding_interval_hours`.
- `plot_funding_rate()` sized its price window and title for 8-hour funding.
- `Ticker.price` and `get_price()` cached prices for 5 minutes; they now cache
  for at most 15 seconds.

### Changed

- `get_funding_rate()`, `get_open_interest()` and `get_long_short_ratio()` fall back
  to Bybit and then OKX when Binance is unreachable or blocked in your region.
  The provider used is in `df.attrs['source']`. Bybit open interest has no USD
  value, so `open_interest_usd` is NaN when Bybit answers.
- Package metadata moved from `setup.py` to `pyproject.toml`; the version has one source.
- The package ships `py.typed`.
- Repository links point to github.com/AnalyticsAscentAkx/crypto-yfinance.

## 0.3.0 — 2026-09-16

### Added

- `Ticker.from_name()` and `Ticker.search()` for discovering current or newly
  launched cryptocurrencies by name, symbol, or CoinGecko ID.
- `register_coin()` for explicitly mapping ambiguous or brand-new symbols.
- Popular newer assets including POL, KAS, TAO, HYPE, ONDO, TRUMP, ENA, AERO,
  PENGU, W, JASMY, and RENDER in the fast local resolver.
- `plot_market_heatmap()` for a market-cap treemap colored by 24-hour movement.
- SMA overlays, optional Bollinger Bands, range buttons, and unified hover on
  candlestick charts.
- `Tickers.plot()` and `Tickers.correlation()` portfolio visualization methods.

### Changed

- Coin discovery now prioritizes exact symbol/name/ID matches and market-cap
  rank, reducing incorrect matches for shared symbols.
- Every chart helper accepts `show=False` and returns its Plotly `Figure`, so
  charts can be embedded in notebooks and apps or exported to HTML/images.
- Chart helpers consistently accept a Plotly `theme` argument.

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
