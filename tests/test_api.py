import importlib
import types
from unittest.mock import Mock

import pandas as pd
import pytest

from cryptofinance import Ticker, clear_cache, download

cache_module = importlib.import_module("cryptofinance.utils.cache")
history_module = importlib.import_module("cryptofinance.utils.get_history")
news_module = importlib.import_module("cryptofinance.utils.get_news")
onchain_module = importlib.import_module("cryptofinance.utils.get_onchain")
defi_module = importlib.import_module("cryptofinance.utils.get_defi_tvl")
plot_module = importlib.import_module("cryptofinance.utils.plot_price")
plots_module = importlib.import_module("cryptofinance.utils.plots")
price_module = importlib.import_module("cryptofinance.utils.get_price")
resolver_module = importlib.import_module("cryptofinance.utils.coingecko_resolver")
search_module = importlib.import_module("cryptofinance.utils.search_symbol")
tickers_module = importlib.import_module("cryptofinance.tickers")
ticker_module = importlib.import_module("cryptofinance.ticker")


@pytest.fixture(autouse=True)
def clean_cache():
    clear_cache()
    yield
    clear_cache()


def frame(value=10, periods=3, freq="1D"):
    return pd.DataFrame({
        "timestamp": pd.date_range("2026-09-01", periods=periods, freq=freq),
        **{field: [value] * periods for field in ("open", "high", "low", "close", "volume")},
    })


def test_price_uses_coingecko_first(monkeypatch):
    client = Mock()
    client.get_price.return_value = {"bitcoin": {"usd": 12345.67}}
    monkeypatch.setattr(price_module, "CoinGeckoAPI", lambda: client)
    monkeypatch.setattr(price_module, "resolve_cg_id", lambda symbol: "bitcoin")
    assert price_module.get_price("BTC_USD") == 12345.67


def test_price_falls_back_to_binance(monkeypatch):
    client = Mock()
    client.get_price.side_effect = RuntimeError("CoinGecko unavailable")
    exchange = Mock()
    exchange.markets = {"BTC/USDT": {}}
    exchange.fetch_ticker.return_value = {"last": 54321.0}
    monkeypatch.setattr(price_module, "CoinGeckoAPI", lambda: client)
    monkeypatch.setattr(price_module.ccxt, "binance", lambda: exchange)
    assert price_module.get_price("BTC_USD") == 54321.0


def test_hourly_history_requests_full_calendar_window(monkeypatch):
    end = 1_800_000_000_000 // 3_600_000 * 3_600_000
    start = end - 7 * 86_400_000
    rows = [[start + i * 3_600_000, 1, 2, 0.5, 1.5, 10] for i in range(168)]
    exchange = Mock(id="binance")
    exchange.fetch_ohlcv.return_value = rows
    monkeypatch.setattr(history_module, "_now_ms", lambda: end + 1)
    result = history_module._exchange_ohlcv(lambda: exchange, "BTC", "USD", "hourly", start, end)
    assert len(result) == 168
    assert exchange.fetch_ohlcv.call_args.kwargs["since"] == start
    assert exchange.fetch_ohlcv.call_args.kwargs["limit"] == 168
    assert result.attrs["actual_symbol"] == "BTC_USDT"


def test_history_rejects_incomplete_window():
    end = 1_800_000_000_000 // 3_600_000 * 3_600_000
    start = end - 7 * 86_400_000
    rows = [[start + i * 3_600_000, 1, 2, 0.5, 1.5, 10] for i in range(7)]
    exchange = Mock(id="binance")
    exchange.fetch_ohlcv.return_value = rows
    with pytest.raises(ValueError, match="expected 168"):
        history_module._exchange_ohlcv(lambda: exchange, "BTC", "USD", "hourly", start, end)


def test_history_rejects_excessive_minute_window():
    with pytest.raises(ValueError, match="at most 7"):
        history_module.get_history("BTC_USD", days=8, interval="1m")


def test_documented_multi_asset_column_access(monkeypatch):
    monkeypatch.setattr(tickers_module, "get_history", lambda *args, **kwargs: frame())
    result = download(["BTC_USD", "ETH_USD"])
    assert result["close"]["BTC_USD"].tolist() == [10, 10, 10]
    assert list(result.columns.names) == ["field", "symbol"]


def test_pairs_with_same_base_are_both_preserved(monkeypatch):
    monkeypatch.setattr(tickers_module, "get_history", lambda *args, **kwargs: frame())
    result = download(["BTC_USD", "BTC_EUR"])
    assert len(result.columns) == 10
    assert {"BTC_USD", "BTC_EUR"} == set(result.columns.get_level_values("symbol"))


def test_space_separated_download_is_multi_asset(monkeypatch):
    monkeypatch.setattr(tickers_module, "get_history", lambda *args, **kwargs: frame())
    result = download("BTC_USD ETH_USD")
    assert set(result.columns.get_level_values("symbol")) == {"BTC_USD", "ETH_USD"}


def test_clear_cache_refreshes_existing_ticker(monkeypatch):
    provider = Mock(side_effect=[{"current_price": 10}, {"current_price": 20}])
    monkeypatch.setattr(ticker_module, "get_info", provider)
    ticker = Ticker("BTC_USD")
    assert ticker.info["current_price"] == 10
    clear_cache()
    assert ticker.info["current_price"] == 20


def test_cached_dataframe_is_copy_safe():
    calls = []

    @cache_module.ttl_cache(ttl=30)
    def provider():
        calls.append(1)
        return frame()

    first = provider()
    first.loc[0, "close"] = -999
    second = provider()
    assert second.loc[0, "close"] == 10
    assert len(calls) == 1


def test_coingecko_fallback_resamples_four_hour_candles_to_daily(monkeypatch):
    day = 86_400_000
    source_step = 14_400_000
    start = 1_800_000_000_000 // day * day
    end = start + 2 * day
    closes = list(range(1, 13))
    # Provider timestamps represent candle close, hence +source_step.
    rows = [[start + (i + 1) * source_step, c, c + 2, c - 1, c + 1]
            for i, c in enumerate(closes)]
    client = Mock()
    client.get_coin_ohlc_by_id.return_value = rows
    monkeypatch.setattr(history_module, "CoinGeckoAPI", lambda: client)
    monkeypatch.setattr(history_module, "resolve_cg_id", lambda symbol: "bitcoin")
    result = history_module._coingecko_ohlcv("BTC", "USD", 2, "daily", start, end)
    assert len(result) == 2
    assert result.loc[0, ["open", "high", "low", "close"]].tolist() == [1, 8, 0, 7]
    assert result["volume"].isna().all()


def test_plot_returns_figure_when_rsi_is_unavailable(monkeypatch):
    monkeypatch.setattr(plot_module, "get_history", lambda *args, **kwargs: frame(periods=2))
    figure = plot_module.plot_price("BTC_USD", days=2, show=False)
    assert figure is not None
    assert len(figure.data) == 2  # candle and volume; RSI omitted


def test_price_plot_adds_moving_averages_and_bollinger(monkeypatch):
    monkeypatch.setattr(plot_module, "get_history", lambda *args, **kwargs: frame(periods=60))
    figure = plot_module.plot_price(
        "BTC_USD", days=60, show_rsi=False, moving_averages=(10, 20),
        show_bollinger=True, show=False,
    )
    names = [trace.name for trace in figure.data]
    assert {"SMA 10", "SMA 20", "Bollinger upper", "Bollinger band"} <= set(names)
    assert figure.layout.hovermode == "x unified"


def test_search_returns_ranked_ready_to_use_pairs(monkeypatch):
    client = Mock()
    client.search.return_value = {"coins": [
        {"id": "small-hype", "symbol": "hype", "name": "Other Hype", "market_cap_rank": 900},
        {"id": "hyperliquid", "symbol": "hype", "name": "Hyperliquid", "market_cap_rank": 20},
    ]}
    monkeypatch.setattr(search_module, "CoinGeckoAPI", lambda: client)
    matches = search_module.search_symbol("HYPE", quote="EUR")
    assert matches[0]["id"] == "hyperliquid"
    assert matches[0]["pair"] == "HYPE_EUR"


def test_ticker_from_name_registers_new_coin(monkeypatch):
    monkeypatch.setattr(ticker_module, "search_symbol", lambda *args, **kwargs: [{
        "id": "brand-new-coin", "symbol": "NEW", "name": "New Coin",
        "market_cap_rank": 123, "pair": "NEW_USD",
    }])
    ticker = Ticker.from_name("New Coin")
    assert ticker.symbol == "new_usd"
    assert resolver_module.CG_ID_MAP["NEW"] == "brand-new-coin"


def test_market_heatmap_returns_figure(monkeypatch):
    monkeypatch.setattr(plots_module, "get_top_coins", lambda **kwargs: pd.DataFrame([
        {"name": "Bitcoin", "symbol": "BTC", "price": 100,
         "market_cap": 1000, "volume_24h": 100, "price_change_pct_24h": 2.5},
        {"name": "Ethereum", "symbol": "ETH", "price": 10,
         "market_cap": 500, "volume_24h": 50, "price_change_pct_24h": -1.0},
    ]))
    figure = plots_module.plot_market_heatmap(show=False)
    assert figure.data[0].type == "treemap"
    assert list(figure.data[0].labels) == ["BTC", "ETH"]


def test_onchain_queries_only_community_metrics(monkeypatch):
    monkeypatch.setattr(onchain_module, "_available_metrics", lambda asset: ["AdrActCnt", "TxCnt"])
    monkeypatch.setattr(onchain_module, "_pages", lambda path, params: iter([{
        "asset": "btc", "time": "2026-09-15T00:00:00Z",
        "AdrActCnt": "10", "TxCnt": "20",
    }]))
    result = onchain_module.get_onchain("BTC", days=7)
    assert result.loc[0, "active_addresses"] == 10
    assert pd.isna(result.loc[0, "nvt_ratio"])
    assert "nvt_ratio" in result.attrs["unavailable_metrics"]


def test_news_filters_rss_by_asset(monkeypatch):
    articles = [
        {"title": "Bitcoin reaches a new level", "published_at": "2026-09-16T10:00:00+00:00",
         "author": None, "url": "https://example.com/btc", "tags": []},
        {"title": "Ethereum upgrade", "published_at": "2026-09-16T11:00:00+00:00",
         "author": None, "url": "https://example.com/eth", "tags": []},
    ]
    monkeypatch.setattr(news_module, "_FEEDS", ("one", "two"))
    monkeypatch.setattr(news_module, "_feed_articles", lambda url: articles)
    assert [item["url"] for item in news_module.get_news("BTC")] == ["https://example.com/btc"]


def test_top_defi_handles_null_tvl(monkeypatch):
    response = Mock()
    response.json.return_value = [
        {"name": "Inactive", "tvl": None},
        {"name": "Active", "tvl": 100},
    ]
    monkeypatch.setattr(defi_module.requests, "get", lambda *args, **kwargs: response)
    result = defi_module.get_top_defi(2)
    assert result["name"].tolist() == ["Active", "Inactive"]


@pytest.mark.parametrize("symbol", ["BTC", "BTC/USD", "BTC_USD_EXTRA", ""])
def test_pair_validation(symbol):
    with pytest.raises(ValueError):
        Ticker(symbol)


def test_funding_annualizes_by_measured_interval(monkeypatch):
    start = 1_800_000_000_000
    rows = [{"fundingTime": start + i * 4 * 3_600_000 + 3, "fundingRate": "0.0001"}
            for i in range(4)]
    funding_module = importlib.import_module("cryptofinance.utils.get_funding_rate")
    monkeypatch.setattr(funding_module, "get_json", lambda *args, **kwargs: rows)
    result = funding_module.get_funding_rate("GTC_USD", limit=3)
    assert len(result) == 3
    assert result["funding_interval_hours"].tolist() == [4, 4, 4]
    assert result["annualized_pct"].iloc[0] == pytest.approx(0.0001 * 6 * 365 * 100)
