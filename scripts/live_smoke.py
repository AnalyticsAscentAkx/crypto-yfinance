"""Live checks against every public provider. Exits 1 if any check fails.

Run weekly in CI to catch provider changes that the deterministic tests cannot.
"""
import sys
from pathlib import Path

# Test this checkout, not an older copy installed in site-packages.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cryptofinance as cf  # noqa: E402

CHECKS = [
    ("price", lambda: cf.get_price("BTC_USD")),
    ("history daily", lambda: cf.get_history("BTC_USD", days=30)),
    ("history hourly", lambda: cf.get_history("ETH_USD", days=2, interval="hourly")),
    ("funding rate", lambda: cf.get_funding_rate("BTC_USD", limit=10)),
    ("open interest", lambda: cf.get_open_interest("BTC_USD", limit=5)),
    ("long/short", lambda: cf.get_long_short_ratio("BTC_USD", limit=5)),
    ("on-chain", lambda: cf.get_onchain("BTC", days=7)),
    ("news", lambda: cf.get_news("BTC_USD", limit=3)),
    ("fear & greed", lambda: cf.get_fear_greed(7)),
    ("top coins", lambda: cf.get_top_coins(10)),
    ("top defi", lambda: cf.get_top_defi(5)),
    ("search", lambda: cf.search_symbol("Hyperliquid", limit=1)),
]


def describe(value):
    rows = len(value) if hasattr(value, "__len__") else 1
    source = getattr(value, "attrs", {}).get("source", "")
    return rows, source


def main():
    failures = 0
    print("| check | result | rows | source |\n|---|---|---|---|")
    for name, check in CHECKS:
        try:
            value = check()
            rows, source = describe(value)
            if not rows:
                raise ValueError("empty result")
            print(f"| {name} | ok | {rows} | {source} |")
        except Exception as exc:
            failures += 1
            print(f"| {name} | FAILED: {str(exc)[:200]} | | |")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
