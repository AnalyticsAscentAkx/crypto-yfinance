# Validation for 0.3.0

Validated on September 16, 2026 before publishing.

- Deterministic suite: 24 tests passed on Python 3.9.6 and Python 3.12.8.
- Optional technical-analysis dependency: `pandas-ta-classic` imported and tested.
- Clean wheel installation: imported version 0.3.0 from `site-packages`; dependency check passed.
- Package validation: wheel and source distribution passed `twine check`.
- PyPI publication verified: a fresh Python 3.9 environment installed version
  `0.3.0` from the public simple index and passed `pip check`.
- Live smoke checks passed for current price, daily history, funding rate, open interest,
  long/short ratio, Coin Metrics on-chain data, RSS news, Fear & Greed, and DeFi ranking.
- Live coin discovery resolved Hyperliquid to `HYPE_USD` / `hyperliquid`; its price,
  history, technical-overlay chart, and the top-20 market heatmap also passed.
- The Python 3.9 interpreter emitted its system-level urllib3/LibreSSL warning; package
  imports and all tests still passed.

The final release artifacts are in `release/0.3.0/`:

- Wheel: `90186ced66dae803e9573f5901e1b56fe8729a941671175f6e8877feee9e4e50`
- Source distribution: `598362975b247b6ee3fa7b324402b7f2bba6d2963893239c6418c47b8eee8f8e`

Recalculate these hashes before upload if any source or packaging file changes.
