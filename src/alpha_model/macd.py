from settings import DATA_PATH
import cudf 
import pandas as pd
import altair as alt
import numpy as np
import pymc as pm
from pytensor.tensor.variable import TensorVariable

# Enable Altair renderers
alt.renderers.enable("browser")
alt.data_transformers.disable_max_rows()


# Load and preprocess data
def load_data(file_path, nrows=None):
    df = pd.read_parquet(file_path)
    df = df.sort_values(by="open_time").reset_index(drop=True)
    df["date"] = pd.to_datetime(df["open_time"], unit="ms")
    df.set_index("date", inplace=True)
    if nrows:
        df = df[:nrows]
    return df


# MACD Implementation
def macd(data, fast_period, slow_period, signal_period):
    """
    Calculate MACD, signal line, and MACD histogram.
    """

    fast_ema = data.ewm(span=fast_period, adjust=False).mean()
    slow_ema = data.ewm(span=slow_period, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    macd_histogram = macd_line - signal_line
    return macd_line, signal_line, macd_histogram


# Backtesting
def backtest(data, macd_params, window):
    """
    Perform backtesting using MACD strategy.
    """
    fast_period, slow_period, signal_period = macd_params
    macd_line, signal_line, macd_histogram = macd(data, *macd_params)
    data = data.iloc[max(fast_period, slow_period, signal_period) :]
    macd_histogram = macd_histogram.iloc[max(fast_period, slow_period, signal_period) :]
    signals = (macd_histogram > 0).astype(int).diff().fillna(0)
    returns = data.pct_change().shift(-1).fillna(0)
    strategy_returns = returns * signals.shift(1).fillna(0)
    rolling_returns = strategy_returns.rolling(window).sum()
    return rolling_returns.sum()


# Bayesian Optimization with pymc3
def optimize_macd(data):
    """
    Optimize MACD parameters using Bayesian Optimization.
    """
    with pm.Model() as model:
        data = pm.Data("data", data)
        fast_period: TensorVariable = pm.DiscreteUniform(
            "fast_period", lower=5, upper=30
        )
        slow_period: TensorVariable = pm.DiscreteUniform(
            "slow_period", lower=20, upper=100
        )
        signal_period: TensorVariable = pm.DiscreteUniform(
            "signal_period", lower=5, upper=20
        )
        window: TensorVariable = pm.DiscreteUniform("window", lower=30, upper=365)

        # Define deterministic objective function to be used for sampling
        def compute_objective(fast_period, slow_period, signal_period, window):
            fast_period_int = int(pm.draw(fast_period))
            slow_period_int = int(pm.draw(slow_period))
            signal_period_int = int(pm.draw(signal_period))
            window_int = int(pm.draw(window))
            macd_params = fast_period, slow_period, signal_period

            return backtest(data, macd_params, window)

        # Add the objective function to the model
        p = pm.Deterministic(
            name="objective",
            var=compute_objective(fast_period, slow_period, signal_period, window),
        )

    return model


# Main execution
if __name__ == "__main__":
    BTCUSDT_1M = DATA_PATH / "output" / "BTCUSDT_1m.parquet"
    df = load_data(BTCUSDT_1M, nrows=10000)
    btc_data = df["close"]
    model = optimize_macd(btc_data)
    np.random.rand(20)



