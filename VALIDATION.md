# Validation for 0.2.1

Validated on September 16, 2026 before publishing.

- Deterministic suite: 20 tests passed on Python 3.9.6 and Python 3.12.8.
- Optional technical-analysis dependency: `pandas-ta-classic` imported and tested.
- Clean wheel installation: imported version 0.2.1 from `site-packages`; dependency check passed.
- Package validation: wheel and source distribution passed `twine check`.
- Live smoke checks passed for current price, daily history, funding rate, open interest,
  long/short ratio, Coin Metrics on-chain data, RSS news, Fear & Greed, and DeFi ranking.
- The Python 3.9 interpreter emitted its system-level urllib3/LibreSSL warning; package
  imports and all tests still passed.

The final release artifacts are in `release/0.2.1/`:

- Wheel: `fa4fb9b31e4f3c37c3a6c4d21378647b70aa746b60ed2d9cae80b4cad4a61374`
- Source distribution: `2fb7ebcd54f641b43d1f77290d30b1519d62857a1f3d5ebed52077230c479092`

Recalculate these hashes before upload if any source or packaging file changes.
