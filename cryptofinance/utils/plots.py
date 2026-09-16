"""
Extra plot functions beyond plot_price.
All charts use Plotly and render in-browser or inline in Jupyter.
"""
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from .get_history import get_history
from .get_fear_greed import get_fear_greed
from .get_dominance import get_dominance
from .get_market_cap import get_market_cap
from .get_funding_rate import get_funding_rate
from .get_onchain import get_onchain
from .get_top_coins import get_top_coins
from .get_defi_tvl import get_top_defi

_THEME = "plotly_dark"


# ─────────────────────────────────────────────────────────────────────────────
# Fear & Greed
# ─────────────────────────────────────────────────────────────────────────────

def plot_fear_greed(days: int = 30) -> None:
    """Gauge chart for today's Fear & Greed index plus a 30-day trend line.

    Parameters
    ----------
    days : days of trend history to show alongside the gauge (default 30)
    """
    df = get_fear_greed(days=max(days, 2))
    latest = df.iloc[-1]
    value = int(latest["value"])
    label = latest["classification"]

    color_map = {
        "Extreme Fear": "#ef5350",
        "Fear":         "#ff7043",
        "Neutral":      "#ffca28",
        "Greed":        "#66bb6a",
        "Extreme Greed":"#26a69a",
    }
    needle_color = color_map.get(label, "#aaa")

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "indicator"}, {"type": "scatter"}]],
        column_widths=[0.35, 0.65],
    )

    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=value,
            title={"text": f"{label}", "font": {"size": 16}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": needle_color, "thickness": 0.25},
                "steps": [
                    {"range": [0, 25],  "color": "#ef5350"},
                    {"range": [25, 45], "color": "#ff7043"},
                    {"range": [45, 55], "color": "#ffca28"},
                    {"range": [55, 75], "color": "#66bb6a"},
                    {"range": [75, 100],"color": "#26a69a"},
                ],
                "threshold": {"line": {"color": "white", "width": 3}, "thickness": 0.75, "value": value},
            },
        ),
        row=1, col=1,
    )

    bar_colors = [color_map.get(c, "#aaa") for c in df["classification"]]
    fig.add_trace(
        go.Bar(x=df["timestamp"], y=df["value"], marker_color=bar_colors, name="Fear & Greed"),
        row=1, col=2,
    )
    fig.add_hline(y=50, line_dash="dot", line_color="white", line_width=0.6, row=1, col=2)

    fig.update_layout(
        template=_THEME,
        title=dict(text=f"Crypto Fear & Greed Index  ·  {days}d", x=0.5),
        showlegend=False,
        height=400,
    )
    fig.show()


# ─────────────────────────────────────────────────────────────────────────────
# Market Dominance
# ─────────────────────────────────────────────────────────────────────────────

def plot_dominance(top_n: int = 8) -> None:
    """Donut chart of market dominance split by asset.

    Parameters
    ----------
    top_n : number of individual assets to show (rest collapsed to 'Others')
    """
    dom = get_dominance()
    sorted_items = sorted(dom.items(), key=lambda x: x[1], reverse=True)
    labels, values = [], []

    for sym, pct in sorted_items[:top_n]:
        labels.append(sym)
        values.append(pct)

    others = sum(v for _, v in sorted_items[top_n:])
    if others > 0:
        labels.append("Others")
        values.append(round(others, 4))

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.52,
        textinfo="label+percent",
        hovertemplate="%{label}: %{value:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        template=_THEME,
        title=dict(text="Crypto Market Dominance", x=0.5),
        height=500,
    )
    fig.show()


# ─────────────────────────────────────────────────────────────────────────────
# Market Cap
# ─────────────────────────────────────────────────────────────────────────────

def plot_market_cap(symbol: str, days: int = 90) -> None:
    """Area chart of a coin's market cap over time.

    Parameters
    ----------
    symbol : e.g. ``'BTC_USD'``
    days   : days of history (default 90)
    """
    df = get_market_cap(symbol, days=days)
    fig = go.Figure(go.Scatter(
        x=df["timestamp"],
        y=df["market_cap"],
        mode="lines",
        fill="tozeroy",
        line=dict(color="#26a69a", width=1.5),
        fillcolor="rgba(38,166,154,0.15)",
        name="Market Cap",
    ))
    fig.update_layout(
        template=_THEME,
        title=dict(text=f"{symbol.upper()} Market Cap  ·  {days}d", x=0.5),
        yaxis_title="Market Cap (USD)",
        height=420,
    )
    fig.show()


# ─────────────────────────────────────────────────────────────────────────────
# Multi-asset price comparison
# ─────────────────────────────────────────────────────────────────────────────

def plot_compare(symbols: list, days: int = 90) -> None:
    """Normalised return comparison for multiple assets.

    All prices are indexed to 100 at the start of the period so you can
    compare percentage performance directly — regardless of price differences.

    Parameters
    ----------
    symbols : list of symbols, e.g. ``['BTC_USD', 'ETH_USD', 'SOL_USD']``
    days    : lookback window (default 90)
    """
    fig = go.Figure()
    for sym in symbols:
        df = get_history(sym, days=days, interval="daily")
        if df.empty or df["close"].iloc[0] == 0:
            continue
        df["indexed"] = df["close"] / df["close"].iloc[0] * 100
        fig.add_trace(go.Scatter(
            x=df["timestamp"],
            y=df["indexed"],
            mode="lines",
            name=sym.split("_")[0].upper(),
            hovertemplate="%{y:.1f}<extra>%{fullData.name}</extra>",
        ))

    fig.add_hline(y=100, line_dash="dot", line_color="white", line_width=0.5)
    fig.update_layout(
        template=_THEME,
        title=dict(text=f"Price Comparison (indexed to 100)  ·  {days}d", x=0.5),
        yaxis_title="Indexed Return",
        height=480,
    )
    fig.show()


# ─────────────────────────────────────────────────────────────────────────────
# Correlation heatmap
# ─────────────────────────────────────────────────────────────────────────────

def plot_correlation(symbols: list, days: int = 90) -> None:
    """Heatmap of pairwise return correlations between assets.

    Values range from -1 (perfectly inverse) to +1 (perfectly correlated).
    Useful for portfolio construction — you want low correlation between holdings.

    Parameters
    ----------
    symbols : list of symbols, e.g. ``['BTC_USD', 'ETH_USD', 'SOL_USD', 'AVAX_USD']``
    days    : lookback window (default 90)
    """
    series = {}
    for sym in symbols:
        df = get_history(sym, days=days, interval="daily")
        label = sym.split("_")[0].upper()
        series[label] = df.set_index("timestamp")["close"]

    combined = pd.DataFrame(series)
    corr = combined.pct_change().dropna().corr().round(2)

    fig = go.Figure(go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.index.tolist(),
        colorscale="RdBu",
        zmid=0,
        zmin=-1, zmax=1,
        text=corr.values,
        texttemplate="%{text}",
        textfont={"size": 13},
        hovertemplate="%{y} vs %{x}: %{z}<extra></extra>",
    ))
    fig.update_layout(
        template=_THEME,
        title=dict(text=f"Return Correlation  ·  {days}d", x=0.5),
        height=500,
    )
    fig.show()


# ─────────────────────────────────────────────────────────────────────────────
# Funding rate
# ─────────────────────────────────────────────────────────────────────────────

def plot_funding_rate(symbol: str, limit: int = 90) -> None:
    """Funding rate bars overlaid with price — spot the squeeze setups.

    Green bars = longs paying shorts (bullish bias).
    Red bars = shorts paying longs (bearish bias).
    Large spikes often precede reversals.

    Parameters
    ----------
    symbol : e.g. ``'BTC_USD'``
    limit  : number of 8h funding periods to show (default 90 ≈ 30 days)
    """
    fr = get_funding_rate(symbol, limit=limit)
    price = get_history(symbol, days=max(limit // 3, 30), interval="daily")

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.55, 0.45],
        subplot_titles=[f"{symbol.upper()} Price", "Funding Rate (8h)"],
    )

    fig.add_trace(
        go.Scatter(x=price["timestamp"], y=price["close"],
                   line=dict(color="#26a69a", width=1.5), name="Price"),
        row=1, col=1,
    )

    colors = ["#26a69a" if v >= 0 else "#ef5350" for v in fr["funding_rate"]]
    fig.add_trace(
        go.Bar(x=fr["timestamp"], y=fr["funding_rate"],
               marker_color=colors, name="Funding Rate"),
        row=2, col=1,
    )
    fig.add_hline(y=0, line_color="white", line_width=0.5, row=2, col=1)

    fig.update_layout(
        template=_THEME,
        title=dict(text=f"{symbol.upper()} Funding Rate", x=0.5),
        showlegend=False,
        height=580,
    )
    fig.show()


# ─────────────────────────────────────────────────────────────────────────────
# On-chain overlay
# ─────────────────────────────────────────────────────────────────────────────

def plot_onchain(symbol: str, metric: str = "active_addresses", days: int = 90) -> None:
    """On-chain metric plotted against price — dual y-axis.

    Parameters
    ----------
    symbol : e.g. ``'BTC_USD'``
    metric : column from ``get_onchain()`` — one of ``'active_addresses'``,
             ``'tx_count'``, ``'transfer_volume_usd'``, ``'nvt_ratio'``,
             ``'hash_rate'``
    days   : lookback window (default 90)
    """
    onchain = get_onchain(symbol.split("_")[0], days=days)
    price = get_history(symbol, days=days, interval="daily")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(x=price["timestamp"], y=price["close"],
                   line=dict(color="#26a69a", width=1.5), name="Price"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=onchain["timestamp"], y=onchain[metric],
                   line=dict(color="#ab47bc", width=1.5), name=metric.replace("_", " ").title()),
        secondary_y=True,
    )

    fig.update_layout(
        template=_THEME,
        title=dict(text=f"{symbol.upper()}  ·  Price vs {metric.replace('_', ' ').title()}", x=0.5),
        height=480,
    )
    fig.update_yaxes(title_text="Price (USD)", secondary_y=False)
    fig.update_yaxes(title_text=metric.replace("_", " ").title(), secondary_y=True)
    fig.show()


# ─────────────────────────────────────────────────────────────────────────────
# Top DeFi protocols
# ─────────────────────────────────────────────────────────────────────────────

def plot_defi_tvl(n: int = 15) -> None:
    """Horizontal bar chart of the top N DeFi protocols by TVL.

    Parameters
    ----------
    n : number of protocols (default 15)
    """
    df = get_top_defi(n=n).sort_values("tvl_usd")
    fig = go.Figure(go.Bar(
        x=df["tvl_usd"],
        y=df["name"],
        orientation="h",
        marker_color="#26a69a",
        hovertemplate="%{y}: $%{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        template=_THEME,
        title=dict(text=f"Top {n} DeFi Protocols by TVL", x=0.5),
        xaxis_title="TVL (USD)",
        height=max(400, n * 28),
    )
    fig.show()


# ─────────────────────────────────────────────────────────────────────────────
# Market snapshot — top coins bubble chart
# ─────────────────────────────────────────────────────────────────────────────

def plot_market_snapshot(n: int = 50) -> None:
    """Bubble chart: market cap vs 24h price change for the top N coins.

    Bubble size = trading volume. Color = positive/negative day.

    Parameters
    ----------
    n : number of coins (default 50)
    """
    df = get_top_coins(n=n).dropna(subset=["price_change_pct_24h", "market_cap", "volume_24h"])

    colors = ["#26a69a" if v >= 0 else "#ef5350" for v in df["price_change_pct_24h"]]

    fig = go.Figure(go.Scatter(
        x=df["market_cap"],
        y=df["price_change_pct_24h"],
        mode="markers+text",
        text=df["symbol"],
        textposition="top center",
        textfont=dict(size=9),
        marker=dict(
            size=df["volume_24h"] / df["volume_24h"].max() * 60 + 6,
            color=colors,
            opacity=0.75,
            line=dict(width=0.5, color="white"),
        ),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Market Cap: $%{x:,.0f}<br>"
            "24h Change: %{y:.2f}%<extra></extra>"
        ),
    ))
    fig.update_xaxes(type="log", title="Market Cap (USD, log scale)")
    fig.add_hline(y=0, line_dash="dot", line_color="white", line_width=0.5)
    fig.update_layout(
        template=_THEME,
        title=dict(text=f"Market Snapshot — Top {n} Coins", x=0.5),
        yaxis_title="24h Price Change (%)",
        height=560,
    )
    fig.show()
