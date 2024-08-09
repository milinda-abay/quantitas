from settings import DATA_PATH
import cudf
import pandas as pd
import talib
from matplotlib import pyplot as plt
import altair as alt
import numpy as np
import pymc as pm


alt.renderers.enable("browser")
alt.data_transformers.disable_max_rows()
BTCUSDT_1M = DATA_PATH / "output" / "BTCUSDT_1m.parquet"

df = pd.read_parquet(BTCUSDT_1M)
df = df.sort_values(by="open_time").reset_index(drop=True)
df["date"] = pd.to_datetime(df["open_time"], unit="ms")
df.set_index("date", inplace=True)

df = df[:10000]
btc_data = df["close"]


# MACD Implementation
def macd(data, fast_period, slow_period, signal_period):
    fast_ema = data.ewm(span=fast_period, adjust=False).mean()
    slow_ema = data.ewm(span=slow_period, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    macd_histogram = macd_line - signal_line
    return macd_line, signal_line, macd_histogram


# Backtesting
def backtest(data, macd_params, window):
    fast_period, slow_period, signal_period = macd_params
    macd_line, signal_line, macd_histogram = macd(
        data, fast_period, slow_period, signal_period
    )
    data = data.iloc[max(fast_period, slow_period, signal_period) :]
    macd_histogram = macd_histogram.iloc[max(fast_period, slow_period, signal_period) :]
    signals = (macd_histogram > 0).astype(int).diff().fillna(0)
    returns = data.pct_change().shift(-1).fillna(0)
    strategy_returns = returns * signals.shift(1).fillna(0)
    rolling_returns = strategy_returns.rolling(window).sum()
    return rolling_returns.sum()


# Bayesian Optimization with pymc3
with pm.Model() as model:
    fast_period = pm.DiscreteUniform("fast_period", lower=5, upper=30)
    slow_period = pm.DiscreteUniform("slow_period", lower=20, upper=100)
    signal_period = pm.DiscreteUniform("signal_period", lower=5, upper=20)
    window = pm.DiscreteUniform("window", lower=30, upper=365)

    # Define deterministic objective function to be used for sampling
    def compute_objective(fast_period, slow_period, signal_period, window):
        macd_params = (int(fast_period), int(slow_period), int(signal_period))
        return backtest(btc_data, macd_params, int(window))

    returns = pm.Deterministic(
        "returns", compute_objective(fast_period, slow_period, signal_period, window)
    )

    # Likelihood (optional; adjust based on your needs)
    likelihood = pm.Normal("likelihood", mu=returns, sd=1, observed=returns)

    # Sample from the posterior
    trace = pm.sample(1000, tune=2000, cores=4)

# Extract integer values from the trace
fast_period_samples = trace["fast_period"]
slow_period_samples = trace["slow_period"]
signal_period_samples = trace["signal_period"]
window_samples = trace["window"]

# Use the sampled parameters with pandas
for i in range(10):  # Example: use a few samples
    fast = int(fast_period_samples[i])
    slow = int(slow_period_samples[i])
    signal = int(signal_period_samples[i])
    window = int(window_samples[i])

    # Calculate MACD with sampled parameters
    macd_line, signal_line, macd_histogram = macd(btc_data, fast, slow, signal)

    # Backtest with sampled parameters
    result = backtest(btc_data, (fast, slow, signal), window)
    print(
        f"Sample {i}: Fast: {fast}, Slow: {slow}, Signal: {signal}, Window: {window}, Result: {result}"
    )
