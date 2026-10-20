# Release 0.3.1

The upload-ready files are in `release/0.3.1/`.

## Before publishing

1. Push this source repository to `https://github.com/AnalyticsAscentAkx/crypto-yfinance`.
2. Confirm the GitHub Actions test matrix passes.
3. Test the package on TestPyPI if this is your first release from this checkout.

## Upload

Use a PyPI API token or configure PyPI Trusted Publishing. Never commit a token.

```bash
python -m pip install --upgrade twine
python -m twine check release/0.3.1/*
python -m twine upload release/0.3.1/*
```

PyPI release filenames are immutable. If an upload partly succeeds, do not rebuild
0.3.1 with different contents; increment the version and build a new release.

## Verify after upload

```bash
python -m venv /tmp/crypto-yfinance-verify
/tmp/crypto-yfinance-verify/bin/python -m pip install crypto-yfinance==0.3.1
/tmp/crypto-yfinance-verify/bin/python -c "import cryptofinance; print(cryptofinance.__version__)"
```
