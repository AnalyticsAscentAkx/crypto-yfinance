from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd

from .get_history import get_history


def plot_price(
    symbol: str,
    days: int = 30,
    interval: str = "daily",
    show_volume: bool = True,
    show_rsi: bool = True,
    theme: str = "plotly_dark",
    show: bool = True,
):
    """Candlestick chart with optional volume and RSI panels.

    Parameters
    ----------
    symbol      : e.g. ``'BTC_USD'``
    days        : number of days to display (default 30)
    interval    : ``'daily'``, ``'hourly'``, ``'4h'``, ``'15m'``
    show_volume : show volume bars below candles (default True)
    show_rsi    : show RSI panel at the bottom (default True, requires pandas-ta)
    theme       : plotly template (default ``'plotly_dark'``)
    show        : display the chart immediately (default True)

    Returns
    -------
    plotly.graph_objects.Figure
    """
    df = get_history(symbol, days=days, interval=interval)

    rsi_series = None
    if show_rsi:
        try:
            try:
                import pandas_ta_classic as ta
            except ImportError:
                import pandas_ta as ta
            tmp = df.set_index("timestamp")
            rsi_series = ta.rsi(tmp["close"], length=14)
            if rsi_series is None or rsi_series.dropna().empty:
                show_rsi = False
                rsi_series = None
            else:
                rsi_series.index = tmp.index
        except ImportError:
            show_rsi = False

    # Build subplot layout
    n_rows = 1 + int(show_volume) + int(show_rsi)
    row_heights = {1: [1.0], 2: [0.65, 0.35], 3: [0.55, 0.25, 0.20]}[n_rows]
    subplot_titles = [symbol.upper()]
    if show_volume:
        subplot_titles.append("Volume")
    if show_rsi:
        subplot_titles.append("RSI (14)")

    fig = make_subplots(
        rows=n_rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=subplot_titles,
    )

    # ── Candlestick ──────────────────────────────────────────────────────────
    fig.add_trace(
        go.Candlestick(
            x=df["timestamp"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
            name="Price",
        ),
        row=1, col=1,
    )

    # ── Volume bars ──────────────────────────────────────────────────────────
    if show_volume:
        vol_row = 2
        colors = [
            "#26a69a" if c >= o else "#ef5350"
            for c, o in zip(df["close"], df["open"])
        ]
        fig.add_trace(
            go.Bar(
                x=df["timestamp"],
                y=df["volume"],
                marker_color=colors,
                name="Volume",
                showlegend=False,
            ),
            row=vol_row, col=1,
        )

    # ── RSI ──────────────────────────────────────────────────────────────────
    if show_rsi and rsi_series is not None:
        rsi_row = 2 + int(show_volume)
        fig.add_trace(
            go.Scatter(
                x=rsi_series.index,
                y=rsi_series.values,
                line=dict(color="#ab47bc", width=1.5),
                name="RSI",
            ),
            row=rsi_row, col=1,
        )
        fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.07, row=rsi_row, col=1)
        fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.07, row=rsi_row, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", line_width=0.8, row=rsi_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", line_width=0.8, row=rsi_row, col=1)

    # ── Layout ───────────────────────────────────────────────────────────────
    fig.update_layout(
        template=theme,
        title=dict(text=f"{symbol.upper()}  ·  {days}d  ·  {interval}", x=0.5),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        margin=dict(l=40, r=40, t=60, b=20),
        height=600 + 100 * (n_rows - 1),
    )
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor="rgba(255,255,255,0.06)")

    if show:
        fig.show()
    return fig
