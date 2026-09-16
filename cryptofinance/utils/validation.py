"""Validation shared by the public data functions."""
import re


def positive_int(value, name, maximum=None):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must be at most {maximum}")
    return value


def asset_symbol(symbol):
    if not isinstance(symbol, str):
        raise ValueError("symbol must be a string such as 'BTC' or 'BTC_USD'")
    parts = symbol.strip().upper().split("_")
    if len(parts) not in (1, 2) or any(not re.fullmatch(r"[A-Z0-9]+", p) for p in parts):
        raise ValueError("Use an asset symbol such as 'BTC' or a pair such as 'BTC_USD'")
    return parts[0]


def split_pair(symbol):
    asset_symbol(symbol)
    parts = symbol.strip().upper().split("_")
    if len(parts) != 2:
        raise ValueError("Use BASE_QUOTE format, for example 'BTC_USD'")
    return tuple(parts)
