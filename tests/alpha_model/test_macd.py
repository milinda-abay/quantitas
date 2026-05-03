import cudf
import numpy as np
import pymc as pm
import pytest

from src.alpha_model.macd import (
    BacktestOp,
    backtest,
    build_model,
    get_map_estimate,
    macd,
)


@pytest.fixture
def price_series() -> cudf.Series:
    """Synthetic upward-trending close price series, 300 rows."""
    np.random.seed(42)
    returns = np.random.normal(0.0001, 0.01, 300)
    prices = 100 * np.exp(np.cumsum(returns))
    return cudf.Series(prices, dtype="float64")


@pytest.fixture
def flat_series() -> cudf.Series:
    """Constant price series — all EMAs equal, histogram zero."""
    return cudf.Series([100.0] * 100, dtype="float64")


# ---------------------------------------------------------------------------
# macd()
# ---------------------------------------------------------------------------


class TestMacd:
    def test_returns_three_series(self, price_series):
        line, signal, histogram = macd(price_series, 12, 26, 9)
        assert isinstance(line, cudf.Series)
        assert isinstance(signal, cudf.Series)
        assert isinstance(histogram, cudf.Series)

    def test_output_length_matches_input(self, price_series):
        line, signal, histogram = macd(price_series, 12, 26, 9)
        assert len(line) == len(price_series)
        assert len(signal) == len(price_series)
        assert len(histogram) == len(price_series)

    def test_histogram_equals_line_minus_signal(self, price_series):
        line, signal, histogram = macd(price_series, 12, 26, 9)
        cudf.testing.assert_series_equal(histogram, line - signal, check_names=False)

    def test_flat_prices_produce_zero_histogram(self, flat_series):
        _, _, histogram = macd(flat_series, 5, 20, 9)
        # After EMAs converge, histogram should be effectively zero
        assert histogram.dropna().abs().max() < 1e-10

    def test_fast_ema_responds_quicker_than_slow(self, price_series):
        # On a rising series the fast EMA should be closer to current price
        line, _, _ = macd(price_series, 5, 50, 9)
        fast_ema = price_series.ewm(span=5, adjust=False).mean()
        slow_ema = price_series.ewm(span=50, adjust=False).mean()
        last_price = price_series.iloc[-1]
        assert abs(fast_ema.iloc[-1] - last_price) < abs(slow_ema.iloc[-1] - last_price)


# ---------------------------------------------------------------------------
# backtest()
# ---------------------------------------------------------------------------


class TestBacktest:
    def test_returns_a_scalar(self, price_series):
        result = backtest(price_series, (12, 26, 9), window=50)
        assert isinstance(float(result), float)

    def test_result_is_finite(self, price_series):
        result = backtest(price_series, (12, 26, 9), window=50)
        assert np.isfinite(float(result))

    def test_different_params_give_different_results(self, price_series):
        result_a = backtest(price_series, (5, 20, 5), window=50)
        result_b = backtest(price_series, (12, 50, 9), window=50)
        assert float(result_a) != float(result_b)

    def test_window_affects_result(self, price_series):
        result_small = backtest(price_series, (12, 26, 9), window=10)
        result_large = backtest(price_series, (12, 26, 9), window=100)
        assert float(result_small) != float(result_large)


# ---------------------------------------------------------------------------
# BacktestOp
# ---------------------------------------------------------------------------


class TestBacktestOp:
    def test_valid_params_return_finite_value(self, price_series):
        op = BacktestOp(price_series, window=50)
        node = None
        outputs = [np.empty(1)]
        op.perform(node, [np.int64(12), np.int64(26), np.int64(9)], outputs)
        assert np.isfinite(outputs[0][0])

    def test_fast_equal_to_slow_returns_penalty(self, price_series):
        op = BacktestOp(price_series, window=50)
        outputs = [np.empty(1)]
        op.perform(None, [np.int64(20), np.int64(20), np.int64(9)], outputs)
        assert outputs[0][0] == pytest.approx(-1e9)

    def test_fast_greater_than_slow_returns_penalty(self, price_series):
        op = BacktestOp(price_series, window=50)
        outputs = [np.empty(1)]
        op.perform(None, [np.int64(30), np.int64(10), np.int64(9)], outputs)
        assert outputs[0][0] == pytest.approx(-1e9)

    def test_output_is_float64_ndarray(self, price_series):
        # PyTensor passes outputs as [[None]] — each element is a single-item list
        op = BacktestOp(price_series, window=50)
        outputs = [[None]]
        op.perform(None, [np.int64(12), np.int64(26), np.int64(9)], outputs)
        assert isinstance(outputs[0][0], np.ndarray)
        assert outputs[0][0].dtype == np.float64


# ---------------------------------------------------------------------------
# build_model()
# ---------------------------------------------------------------------------


class TestBuildModel:
    def test_returns_pymc_model(self, price_series):
        model, _ = build_model(price_series, window=50)
        assert isinstance(model, pm.Model)

    def test_returns_backtest_op(self, price_series):
        _, bt_op = build_model(price_series, window=50)
        assert isinstance(bt_op, BacktestOp)

    def test_model_has_expected_free_vars(self, price_series):
        model, _ = build_model(price_series, window=50)
        names = {v.name for v in model.free_RVs}
        assert "fast_period" in names
        assert "slow_period" in names
        assert "signal_period" in names

    def test_model_has_no_window_free_var(self, price_series):
        model, _ = build_model(price_series, window=50)
        names = {v.name for v in model.free_RVs}
        assert "window" not in names


# ---------------------------------------------------------------------------
# get_map_estimate()
# ---------------------------------------------------------------------------


class TestGetMapEstimate:
    @pytest.fixture
    def short_trace(self, price_series):
        """Run a minimal sample to get a trace for MAP tests."""
        model, _ = build_model(price_series, window=50)
        with model:
            trace = pm.sample(
                draws=100,
                tune=50,
                step=pm.Metropolis(),
                cores=1,
                progressbar=False,
                return_inferencedata=True,
            )
        return trace

    def test_returns_three_integers(self, short_trace):
        result = get_map_estimate(short_trace)
        assert len(result) == 3
        assert all(isinstance(v, int) for v in result)

    def test_fast_period_within_prior_bounds(self, short_trace):
        fast, _, _ = get_map_estimate(short_trace)
        assert 5 <= fast <= 29

    def test_slow_period_within_prior_bounds(self, short_trace):
        _, slow, _ = get_map_estimate(short_trace)
        assert 6 <= slow <= 100

    def test_signal_period_within_prior_bounds(self, short_trace):
        _, _, signal = get_map_estimate(short_trace)
        assert 5 <= signal <= 20

    def test_fast_strictly_less_than_slow(self, short_trace):
        fast, slow, _ = get_map_estimate(short_trace)
        assert fast < slow
