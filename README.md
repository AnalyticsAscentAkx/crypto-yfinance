# crypto-yfinance

[![PyPI version](https://badge.fury.io/py/crypto-yfinance.svg)](https://pypi.org/project/crypto-yfinance/)
[![Downloads](https://pepy.tech/badge/crypto-yfinance)](https://pepy.tech/project/crypto-yfinance)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Built by [Aakash Chavan Ravindranath](https://www.linkedin.com/in/aakashcr/) · [Medium](https://medium.com/@craakash)**

---

I got tired of stitching together five different libraries every time I wanted to do proper crypto analysis. Price data from one place, on-chain metrics from another, funding rates somewhere else, and a random script I found online for fear & greed. It was a mess, and I kept rewriting the same boilerplate code in every project.

So I built this. One library that handles all of it — market data, derivatives, on-chain metrics, DeFi TVL, sentiment, technical indicators, and charts. You shouldn't need to install separate libraries just to answer a simple question about Bitcoin.

The API design is heavily inspired by `yfinance`. If you've used that, you'll feel right at home.

---

## What's inside

| Category | What you get |
|---|---|
| **Market Data** | Real-time prices, OHLCV history, market cap, volume, coin profiles |
| **Derivatives** | Funding rates, open interest, long/short ratios (Binance Futures) |
| **On-Chain** | Active addresses, NVT ratio, transaction volume, hash rate (CoinMetrics) |
| **DeFi** | Protocol TVL, top protocols, TVL by chain (DeFiLlama) |
| **Sentiment** | Fear & Greed Index with full history |
| **Technical Analysis** | RSI, MACD, Bollinger Bands, EMA, ATR, OBV built-in |
| **Plots** | 10 chart types — candlestick, market heatmap, correlation, dominance, funding rate, and more |

No API key is required. The package uses public provider endpoints. You can set
`COINGECKO_DEMO_API_KEY` to improve CoinGecko rate limits, but it is optional.

---

## Install

```bash
pip install crypto-yfinance
```

For technical indicators (RSI, MACD, etc.):

```bash
pip install "crypto-yfinance[ta]"
```

---

## Quick start

```python
from cryptofinance import Ticker

t = Ticker('BTC_USD')

# Price and history
print(t.price)
df = t.history(days=90)

# Full coin profile
print(t.info['ath'])
print(t.info['twitter_followers'])

# Derivatives
print(t.funding_rate)
print(t.long_short_ratio)

# On-chain metrics
print(t.onchain)

# Built-in chart
t.plot(days=60)
```

---

## The Ticker object

This is the main way to use the library. It bundles everything for a single asset into one clean interface.

```python
from cryptofinance import Ticker

t = Ticker('ETH_USD')
```

**Supported symbol format:** `BASE_QUOTE`, e.g. `BTC_USD`, `ETH_USDT`, `SOL_USD`

### Properties

```python
t.price              # float — current spot price
t.fast_info          # dict — price, market cap, 24h/7d change, rank, ATH
t.info               # dict — full profile (description, links, social, dev stats)
t.market_cap         # DataFrame — 30-day market cap history
t.volume             # DataFrame — 30-day volume history
t.dominance          # float — % of total crypto market cap

t.funding_rate       # DataFrame — 8h funding rate history (Binance Futures)
t.open_interest      # DataFrame — open interest history (Binance Futures)
t.long_short_ratio   # DataFrame — long vs short account ratio

t.onchain            # DataFrame — active addresses, NVT, tx count, hash rate
t.news               # list — recent news articles
```

### Methods

```python
t.history(days=30, interval='daily')    # DataFrame — OHLCV
# interval options: 'daily', 'hourly', '4h', '15m', '5m', '1m'

t.technicals(days=90)                   # DataFrame — OHLCV + RSI, MACD, BB, ATR, OBV
# requires: pip install "crypto-yfinance[ta]"

t.plot(days=30, interval='daily')       # candlestick + volume + RSI chart
t.plot(show_rsi=False)                  # candlestick + volume only
t.plot(show_bollinger=True)             # add Bollinger Bands
t.plot(moving_averages=(10, 20, 50))    # choose SMA overlays
t.plot(show=False)                      # return a Plotly figure without displaying it
```

### Find new cryptocurrencies

Coin discovery is live, so newly launched assets do not need to be hard-coded
in a package release:

```python
from cryptofinance import Ticker, search_symbol, register_coin

Ticker.search('hyperliquid')
# [{'id': 'hyperliquid', 'symbol': 'HYPE', 'name': 'Hyperliquid',
#   'market_cap_rank': ..., 'pair': 'HYPE_USD'}]

hype = Ticker.from_name('hyperliquid')
print(hype.symbol, hype.coingecko_id, hype.price)

# Resolve a shared or extremely new symbol explicitly when needed
register_coin('MYCOIN', 'my-coingecko-id')
coin = Ticker('MYCOIN_USD')
```

Search accepts a coin name, ticker symbol, or CoinGecko ID. Exact matches are
ranked by market cap to reduce ambiguity when several projects share a symbol.

`days` always means calendar days, including for intraday intervals. History
contains complete, closed candles and uses timezone-naive UTC candle-open times.
The returned DataFrame's `attrs` records the provider, requested/actual pair,
interval, volume unit, and fetch time. For example, Binance serves `BTC_USD`
through its `BTC_USDT` market and records that substitution in the metadata.
To keep public-API requests bounded, maximum lookbacks are 10 years for daily,
365 days for hourly, 730 days for 4-hour, 90 days for 15-minute, 30 days for
5-minute, and 7 days for 1-minute candles.

---

## Multiple assets — Tickers and download()

```python
from cryptofinance import Tickers, download

# Tickers object
t = Tickers(['BTC_USD', 'ETH_USD', 'SOL_USD', 'AVAX_USD'])
t['BTC_USD'].info         # access individual Ticker
t.history(days=30)        # combined multi-level DataFrame
t.prices()                # {'BTC_USD': 95420.0, 'ETH_USD': 3210.5, ...}
t.fast_info()             # summary table for all assets
t.plot(days=90)           # indexed performance comparison
t.correlation(days=90)    # return-correlation heatmap

# Or use download() directly
df = download('BTC_USD', days=90)
df = download(['BTC_USD', 'ETH_USD', 'SOL_USD'], days=30)
df['close']['BTC_USD']    # multi-level column access
```

---

## API Reference

### Market data

```python
from cryptofinance import (
    get_price, get_history, get_market_cap, get_volume,
    get_info, get_trending, get_top_coins, get_global, get_dominance, get_news
)

get_price('BTC_USD')
# → 95420.5

get_history('BTC_USD', days=90, interval='daily')
# → DataFrame: timestamp, open, high, low, close, volume

get_market_cap('ETH_USD', days=60)
# → DataFrame: timestamp, market_cap

get_volume('SOL_USD', days=30)
# → DataFrame: timestamp, volume

get_info('BTC_USD')
# → dict: name, rank, description, ath, atl, twitter_followers,
#         reddit_subscribers, github_stars, coingecko_score, ...

get_trending()
# → list of 7 trending coins with name, symbol, market_cap_rank, price_btc

get_top_coins(n=50, currency='usd')
# → DataFrame: rank, name, symbol, price, market_cap, volume_24h,
#              price_change_pct_24h, ath, circulating_supply

get_global()
# → dict: total_market_cap_usd, total_volume_24h_usd, btc_dominance,
#         eth_dominance, market_cap_change_pct_24h, active_cryptocurrencies

get_dominance()
# → {'BTC': 52.4, 'ETH': 17.1, 'BNB': 3.2, ...}

get_news('BTC', limit=10)
# → list of dicts: title, published_at, author, url, tags
```

News comes from recent public RSS headlines and can return fewer than `limit`
matching articles. It does not download full article content.

### Sentiment

```python
from cryptofinance import get_fear_greed

df = get_fear_greed(days=30)
# → DataFrame: timestamp, value (0-100), classification
# Classifications: Extreme Fear / Fear / Neutral / Greed / Extreme Greed
```

### Derivatives

These pull from the Binance Futures public API — no account or API key needed.

```python
from cryptofinance import get_funding_rate, get_open_interest, get_long_short_ratio

get_funding_rate('BTC_USD', limit=100)
# → DataFrame: timestamp, funding_rate, annualized_pct
# Positive = longs paying shorts. Negative = shorts paying longs.

get_open_interest('BTC_USD', period='1d', limit=30)
# → DataFrame: timestamp, open_interest, open_interest_usd

get_long_short_ratio('BTC_USD', period='1d', limit=30)
# → DataFrame: timestamp, long_short_ratio, long_pct, short_pct
```

### On-chain

Powered by the [CoinMetrics Community API](https://coinmetrics.io/community-network-data/) — free, no key needed.

```python
from cryptofinance import get_onchain

df = get_onchain('BTC', days=90)
# → DataFrame: timestamp, active_addresses, tx_count, transfer_volume_usd,
#              nvt_ratio, hash_rate, mean_fee_native, block_count
```

Coin Metrics exposes a different Community metric set for each asset. Columns
without Community access are `NaN` and listed in
`df.attrs['unavailable_metrics']`; the library does not estimate them.

**What these metrics mean:**

- `active_addresses` — unique addresses active on-chain each day. A growing network = growing adoption.
- `tx_count` — transaction count. Measures actual usage, not just price.
- `nvt_ratio` — Network Value to Transactions. Think of it like a P/E ratio for crypto. High NVT = price is running ahead of on-chain activity.
- `hash_rate` — mining power securing the network (PoW chains only). Higher = more secure and more miner confidence.

### DeFi

Powered by [DeFiLlama](https://defillama.com) — fully free.

```python
from cryptofinance import get_defi_tvl, get_top_defi, get_tvl_by_chain

get_defi_tvl('uniswap')
# → DataFrame: timestamp, tvl_usd
# Works with: 'aave', 'curve', 'lido', 'makerdao', 'compound', 'pancakeswap', ...

get_top_defi(n=20)
# → DataFrame: name, symbol, tvl_usd, chain, category, change_1h, change_1d, change_7d

get_tvl_by_chain()
# → DataFrame: chain, tvl_usd  (sorted by TVL)
```

### Gas

```python
from cryptofinance import get_gas

get_gas()
# → {'slow': 8.5, 'standard': 12.0, 'fast': 18.0, 'rapid': 25.0, 'unit': 'gwei', 'source': '...'}
```

### Technical indicators

```python
from cryptofinance import get_technicals
# requires: pip install "crypto-yfinance[ta]"

df = get_technicals('BTC_USD', days=90)
# → OHLCV DataFrame enriched with:
#   EMA_20, EMA_50, SMA_200
#   RSI_14
#   MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
#   BBL_20_2.0, BBM_20_2.0, BBU_20_2.0
#   ATRr_14
#   OBV
```

---

## Charts

All charts are interactive Plotly figures that open in your browser or render inline in Jupyter.

```python
from cryptofinance import (
    plot_price, plot_fear_greed, plot_dominance, plot_market_cap,
    plot_compare, plot_correlation, plot_funding_rate,
    plot_onchain, plot_defi_tvl, plot_market_snapshot, plot_market_heatmap
)

# Candlestick + volume + RSI (3 panels)
plot_price('BTC_USD', days=60, interval='daily')
plot_price('ETH_USD', days=7, interval='hourly', show_rsi=False)
plot_price('SOL_USD', days=90, moving_averages=(20, 50), show_bollinger=True)

# Fear & Greed gauge + 30-day bar chart
plot_fear_greed(days=30)

# Donut chart of market dominance
plot_dominance(top_n=8)

# Market cap area chart
plot_market_cap('BTC_USD', days=180)

# Normalised performance comparison
plot_compare(['BTC_USD', 'ETH_USD', 'SOL_USD', 'AVAX_USD'], days=90)

# Return correlation heatmap — useful for portfolio construction
plot_correlation(['BTC_USD', 'ETH_USD', 'SOL_USD', 'LINK_USD'], days=90)

# Funding rate bars + price overlay
plot_funding_rate('BTC_USD', limit=90)

# On-chain metric vs price (dual y-axis)
plot_onchain('BTC_USD', metric='active_addresses', days=90)
plot_onchain('BTC_USD', metric='nvt_ratio', days=180)

# Top DeFi protocols by TVL
plot_defi_tvl(n=15)

# Bubble chart: market cap vs 24h change, sized by volume
plot_market_snapshot(n=50)

# Market-cap treemap, colored by 24-hour performance
plot_market_heatmap(n=50)
```

Every chart returns a Plotly `Figure`. Pass `show=False` to embed or export it:

```python
fig = plot_market_heatmap(n=100, show=False)
fig.write_html('crypto-market.html')
```

---

## Caching

By default, results are cached in-memory with sensible TTLs so you don't hammer APIs repeatedly in the same session:

- Prices: 5 minutes
- OHLCV history: 5 minutes
- Coin info: 10 minutes
- Fear & Greed: 1 hour
- On-chain metrics: 1 hour
- News: 15 minutes

To clear the cache manually:

```python
from cryptofinance import clear_cache
clear_cache()
```

## Optional diagnostics

The library is quiet by default. To see provider fallbacks and HTTP retries:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('cryptofinance').setLevel(logging.DEBUG)
```

---

## Data sources

| Source | What it powers | Cost |
|---|---|---|
| [CoinGecko](https://coingecko.com) | Prices, OHLCV, market cap, info, trending | Free |
| [Binance](https://binance.com) | OHLCV (primary), funding rates, open interest, long/short | Free |
| [CoinMetrics](https://coinmetrics.io) | On-chain metrics (active addresses, NVT, hash rate) | Free |
| [DeFiLlama](https://defillama.com) | DeFi TVL by protocol and chain | Free |
| [alternative.me](https://alternative.me/crypto/fear-and-greed-index/) | Fear & Greed Index | Free |
| [CoinDesk](https://www.coindesk.com/) and [Cointelegraph](https://cointelegraph.com/) | News headline metadata via RSS | Free |

---

## Contributing

Issues and PRs are welcome at [github.com/craakash/crypto-yfinance](https://github.com/craakash/crypto-yfinance).

If something is broken or you want a feature added, open an issue and I'll try to get to it.

---

## License

MIT — do whatever you want with it.

See the [changelog](https://github.com/craakash/crypto-yfinance/blob/main/CHANGELOG.md)
for release-by-release changes.
