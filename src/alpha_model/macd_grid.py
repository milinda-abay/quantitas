from __future__ import annotations

import itertools
from pathlib import Path
from typing import cast

import altair as alt
import cudf
import numpy as np

from settings import DATA_PATH

alt.renderers.enable("browser")
alt.data_transformers.disable_max_rows()


def load_data(file_path: Path | str, nrows: int | None = None) -> cudf.DataFrame:
    df = cudf.read_parquet(file_path)
    df = df.sort_values(by="open_time").reset_index(drop=True)
    df["date"] = cudf.to_datetime(df["open_time"], unit="ms")
    df.set_index("date", inplace=True)
    if nrows:
        df = df[:nrows]
    return df


def macd(
    data: cudf.Series,
    fast_period: int,
    slow_period: int,
    signal_period: int,
) -> tuple[cudf.Series, cudf.Series, cudf.Series]:
    """Calculate MACD, signal line, and MACD histogram."""
    fast_ema = data.ewm(span=fast_period, adjust=False).mean()
    slow_ema = data.ewm(span=slow_period, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    macd_histogram = macd_line - signal_line
    return macd_line, signal_line, macd_histogram


def backtest(
    data: cudf.Series,
    fast_period: int,
    slow_period: int,
    signal_period: int,
    window: int,
) -> float:
    """Backtest MACD strategy; returns scalar total rolling strategy return."""
    _, _, macd_histogram = macd(data, fast_period, slow_period, signal_period)
    warmup = max(fast_period, slow_period, signal_period)
    data_trimmed = data.iloc[warmup:]
    macd_histogram = macd_histogram.iloc[warmup:]
    signals = (macd_histogram > 0).astype(int).diff().fillna(0)
    returns = data_trimmed.pct_change().shift(-1).fillna(0)
    strategy_returns = returns * signals.shift(1).fillna(0)
    rolling_returns = strategy_returns.rolling(window).sum()
    result = float(rolling_returns.sum())
    return result if np.isfinite(result) else -1e9


def grid_search(
    series: cudf.Series,
    fast_range: range = range(5, 30),
    slow_range: range = range(6, 101),
    signal_range: range = range(5, 21),
    window: int = 252,
) -> cudf.DataFrame:
    """
    Exhaustive grid search over all valid MACD parameter combinations (fast < slow).
    Returns a cudf DataFrame of results sorted by backtest return descending.
    """
    fasts, slows, signals, returns = [], [], [], []
    pairs = [(f, s) for f, s in itertools.product(fast_range, slow_range) if f < s]
    total = len(pairs) * len(signal_range)
    print(f"Evaluating {total:,} parameter combinations...")

    count = 0
    for fast, slow in pairs:
        for signal in signal_range:
            ret = backtest(series, fast, slow, signal, window)
            fasts.append(fast)
            slows.append(slow)
            signals.append(signal)
            returns.append(ret)
            count += 1
            if count % 100 == 0:
                print(f"  {count:,}/{total:,} ({100 * count / total:.1f}%)")

    results = cudf.DataFrame(
        {
            "fast_period": fasts,
            "slow_period": slows,
            "signal_period": signals,
            "backtest_return": returns,
        }
    )
    return results.sort_values("backtest_return", ascending=False).reset_index(
        drop=True
    )


def best_params(results: cudf.DataFrame) -> tuple[int, int, int]:
    """Return the (fast, slow, signal) with the highest backtest return."""
    top = results.iloc[0]
    return int(top["fast_period"]), int(top["slow_period"]), int(top["signal_period"])


if __name__ == "__main__":
    BTCUSDT_1M = DATA_PATH / "output" / "BTCUSDT_1m.parquet"
    df = load_data(BTCUSDT_1M, nrows=300_000)
    series = cast(cudf.Series, df["close"])

    print("Running exhaustive grid search for MACD parameters...")
    results = grid_search(series, window=252)

    fast_best, slow_best, signal_best = best_params(results)
    print(f"\nBest Parameters:")
    print(f"  fast_period   = {fast_best}")
    print(f"  slow_period   = {slow_best}")
    print(f"  signal_period = {signal_best}")
    print(f"  Backtest return: {float(results.iloc[0]['backtest_return']):.4f}")

    print("\nTop 10 parameter combinations:")
    print(results.head(10).to_pandas().to_string(index=False))

    top_n = results.head(200).to_pandas()
    charts = []
    for param in ["fast_period", "slow_period", "signal_period"]:
        chart = (
            alt.Chart(top_n)
            .mark_bar()
            .encode(
                x=alt.X(f"{param}:O", title=param),
                y=alt.Y("count():Q", title="Count in top 200"),
            )
            .properties(title=param, width=200)
        )
        charts.append(chart)

    (
        alt.hconcat(*charts).properties(
            title="MACD Grid Search — Top 200 Parameter Frequency"
        )
    ).show()
