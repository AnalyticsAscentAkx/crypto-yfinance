# Validation for 0.3.1

Validated on October 20, 2026 before publishing.

- Deterministic suite: 28 tests passed on Python 3.9.6 and Python 3.11.
- Clean wheel installation on Python 3.9.6: imported version 0.3.1 from `site-packages`;
  `pip check` passed.
- Package validation: wheel and source distribution passed `twine check` (twine 6.2.0).
- The wheel built from `pyproject.toml` alone has the same file list as 0.3.0, plus `py.typed`.
- Live smoke checks (`scripts/live_smoke.py`) passed for price, daily and hourly history,
  funding rate, open interest, long/short ratio, Coin Metrics on-chain data, RSS news,
  Fear & Greed, top coins, DeFi ranking and coin search.
- Each derivatives provider was called directly for BTC_USD: Binance, Bybit and OKX all
  returned funding, open interest and long/short rows in matching units.
- Funding intervals were checked against Binance `fundingInfo`: BTCUSDT measured 8 hours
  and GTCUSDT measured 4 hours, matching the exchange's published settings.
- Region fallback: the `live providers` workflow on a GitHub US runner (run 39446858988)
  passed all 12 checks. Binance and Bybit were unavailable there; history came from
  Coinbase and funding, open interest and long/short from OKX.

The final release artifacts are in `release/0.3.1/`:

- Wheel: `44f8bb63ebb33e69f66999ad5088797c35f6cbc8bedc78069b930121a1d00f39`
- Source distribution: `f4bad08f5e882f25adb4fe02dd04cc3a39252fbc4fc2cdd2a800e7a9b1885e3f`

Recalculate these hashes before upload if any source or packaging file changes.
