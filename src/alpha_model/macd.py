from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence, Union, cast

from settings import DATA_PATH
import cudf
import pandas as pd
import altair as alt
import numpy as np
import numpy.typing as npt
import pymc as pm
import arviz as az
from pytensor.tensor.type import lscalar, dscalar
from pytensor.graph.op import Op

Series = Union[cudf.Series, pd.Series]

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
    data: Series,
    fast_period: int,
    slow_period: int,
    signal_period: int,
) -> tuple[Series, Series, Series]:
    """Calculate MACD, signal line, and MACD histogram."""
    fast_ema = data.ewm(span=fast_period, adjust=False).mean()
    slow_ema = data.ewm(span=slow_period, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    macd_histogram = macd_line - signal_line
    return macd_line, signal_line, macd_histogram


def backtest(
    data: Series,
    macd_params: tuple[int, int, int],
    window: int,
) -> float:
    """Backtest MACD strategy; returns scalar total rolling strategy return."""
    fast_period, slow_period, signal_period = macd_params
    macd_line, signal_line, macd_histogram = macd(data, *macd_params)
    data = data.iloc[max(fast_period, slow_period, signal_period) :]
    macd_histogram = macd_histogram.iloc[max(fast_period, slow_period, signal_period) :]
    signals = (macd_histogram > 0).astype(int).diff().fillna(0)
    returns = data.pct_change().shift(-1).fillna(0)
    strategy_returns = returns * signals.shift(1).fillna(0)
    rolling_returns = strategy_returns.rolling(window).sum()
    return rolling_returns.sum()


class BacktestOp(Op):
    """
    PyTensor Op wrapping backtest() for use in a PyMC model.

    Bridges PyMC's symbolic computation graph and the Python backtest function,
    which is non-differentiable and can't be expressed as PyTensor primitives.
    """

    itypes = [lscalar, lscalar, lscalar]  # int64 — DiscreteUniform outputs int64
    otypes = [dscalar]

    def __init__(self, series: cudf.Series, window: int):
        self.series = series.to_pandas()
        self.window = window

    def perform(
        self,
        node: Any,
        inputs: Sequence[Any],
        output_storage: list[list[npt.NDArray[np.float64] | None]],
    ) -> None:
        fast, slow, signal = [int(x) for x in inputs]
        if fast >= slow:
            output_storage[0][0] = np.array(-1e9, dtype=np.float64)
            return
        result = backtest(self.series, (fast, slow, signal), self.window)
        if not np.isfinite(float(result)):
            output_storage[0][0] = np.array(-1e9, dtype=np.float64)
        else:
            output_storage[0][0] = np.array(float(result), dtype=np.float64)


def build_model(series: cudf.Series, window: int = 252) -> tuple[pm.Model, BacktestOp]:
    """
    Build the PyMC model for Bayesian MACD parameter optimization.

    The model defines DiscreteUniform priors over (fast, slow, signal) periods
    and uses the backtest return as an unnormalized log-likelihood via pm.Potential.
    Metropolis MCMC will sample parameter combinations proportional to their
    backtest performance, yielding a posterior over good-performing parameters.
    """
    bt_op = BacktestOp(series, window)
    with pm.Model() as model:
        fast = pm.DiscreteUniform("fast_period", lower=5, upper=29)
        slow = pm.DiscreteUniform("slow_period", lower=6, upper=100)
        signal = pm.DiscreteUniform("signal_period", lower=5, upper=20)
        pm.Potential("likelihood", bt_op(fast, slow, signal))
    return model, bt_op


def run_optimization(
    series: cudf.Series,
    draws: int = 2000,
    tune: int = 1000,
    window: int = 252,
    chains: int = 10,
) -> tuple[az.InferenceData, BacktestOp]:
    """
    Run Metropolis MCMC to sample MACD parameters from the posterior.

    Returns InferenceData (ArviZ) and the BacktestOp for downstream evaluation.
    cores=1 is required because BacktestOp closes over a pandas Series
    which is not safely picklable across processes.
    """
    model, bt_op = build_model(series, window=window)
    with model:
        trace = pm.sample(
            draws=draws,
            tune=tune,
            chains=chains,
            step=pm.Metropolis(),
            cores=chains,
            return_inferencedata=True,
            progressbar=True,
        )
    return trace, bt_op


def get_map_estimate(trace: az.InferenceData) -> tuple[int, int, int]:
    """
    Extract MAP (mode of posterior) parameter estimates from the trace.

    Uses mode rather than mean because discrete integer parameters can't
    have fractional-valued MAP estimates.
    """
    posterior = trace.posterior  # type: ignore

    def _mode(da) -> int:
        flat = da.values.flatten()
        vals, counts = np.unique(flat, return_counts=True)
        return int(vals[np.argmax(counts)])

    return (
        _mode(posterior["fast_period"]),
        _mode(posterior["slow_period"]),
        _mode(posterior["signal_period"]),
    )


if __name__ == "__main__":
    BTCUSDT_1M = DATA_PATH / "output" / "BTCUSDT_1m.parquet"
    df = load_data(BTCUSDT_1M, nrows=300_000)
    series = cast(cudf.Series, df["close"])

    print("Running Bayesian MACD parameter optimization...")
    trace, bt_op = run_optimization(series, draws=4000, tune=1500, window=252)

    fast_map, slow_map, signal_map = get_map_estimate(trace)
    print(f"\nMAP Parameters:")
    print(f"  fast_period   = {fast_map}")
    print(f"  slow_period   = {slow_map}")
    print(f"  signal_period = {signal_map}")

    map_return = backtest(series, (fast_map, slow_map, signal_map), window=252)
    print(f"  Backtest return at MAP: {map_return:.4f}")

    print("\nPosterior Summary:")
    print(az.summary(trace, var_names=["fast_period", "slow_period", "signal_period"]))

    posterior = trace.posterior  # type: ignore
    rows = []
    for param in ["fast_period", "slow_period", "signal_period"]:
        flat = posterior[param].values.flatten()
        vals, counts = np.unique(flat, return_counts=True)
        for v, c in zip(vals, counts):
            rows.append({"parameter": param, "value": int(v), "count": int(c)})

    chart = (
        alt.Chart(cudf.DataFrame(rows).to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("value:O", title="Value"),
            y=alt.Y("count:Q", title="Posterior Samples"),
            color=alt.Color("parameter:N", legend=None),
            tooltip=["parameter:N", "value:O", "count:Q"],
        )
        .facet(facet="parameter:N", columns=3)
        .properties(title="MACD Parameter Posterior Distributions")
    )
    chart.show()
