# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Quantitas is a quantitative trading system modelled on the framework from *Inside the Black Box* (Rishi K. Narang): alpha model → risk model → transaction cost model → portfolio construction model → execution model. Currently the alpha model layer is the most developed.

## Environment

The project runs inside a **Dev Container** (`.devcontainer/`) built on RAPIDS (`cudf`), requiring an NVIDIA GPU with CUDA 12.2. The container mounts the host path `F:\data` to `/workspaces/quantitas/data`.

Set `PYTHONPATH=/workspaces/quantitas` (already done by devcontainer settings) so that top-level package imports (`from settings import ...`, `from src...`, etc.) resolve correctly.

Required env variable: `BINANCE_API_KEY` (consumed via `settings/env_variables.py`).

## Running Code

```bash
# Run a module directly from project root
python src/alpha_model/indicators.py
python src/alpha_model/macd.py

# Process ALL tickers and intervals into parquet (preferred)
python input/process/etl/pipeline.py

# Legacy single-ticker processor (BTCUSDT 1s/1m only)
python input/process/btcusdt_binance.py

# Download historical kline data from Binance
python binance_public_data/download-kline.py
```

There is no test suite or lint configuration currently.

## Architecture

```
settings/          # Shared config imported everywhere via `from settings import ...`
  constants.py     # SYMBOLS, date ranges, KLINE_COL_NAMES, URL bases
  enums.py         # Intervals, Months, Years, TradingType
  folders.py       # Path constants: BASE_PATH, DATA_PATH, DAILY_KLINES, MONTHLY_KLINES
  env_variables.py # BINANCE_API_KEY from env

src/alpha_model/
  indicators.py    # Pure pandas: SMA, MACD oscillator, Bollinger Bands, Chaikin Money Flow
  signals.py       # Signal generation from indicators (MACD crossover, Bollinger breakout)
  macd.py          # EMA-based MACD + PyMC Bayesian parameter optimisation
  web_socket.py    # Binance WebSocket streams (both websockets and websocket-client libs)

input/process/
  etl/               # SOLID ETL pipeline — processes all tickers × intervals
    pipeline.py      # Entry point: wires components, purges .zip.* partials, runs loop
    discovery.py     # KlineDiscovery: scans data/spot/ for (ticker, interval) pairs → KlineSource
    readers.py       # KlineReader ABC + CsvKlineReader + ZipKlineReader + CompositeKlineReader
    transformer.py   # KlineTransformer: concat, dedup on open_time, sort, convert_dtypes
    writer.py        # KlineWriter: writes data/output/{TICKER}_{INTERVAL}.parquet
  btcusdt_binance.py # Legacy: hardcoded BTCUSDT 1s/1m processor (superseded by etl/)

utils/
  functions.py     # lower_underscore(): sanitises column names for parquet output

scripts/           # Standalone research/exploration scripts (PyMC, Bayesian A/B)
binance_public_data/ (and binance-public-data/)  # Binance public data download utilities
data/              # Not in git; mounted from host. Structure: spot/daily|monthly/klines/<SYMBOL>/<interval>/
```

## Data Flow

1. **Ingest**: `binance_public_data/download-kline.py` fetches zip/csv files from `data.binance.vision` into `data/spot/`.
2. **Process**: `input/process/etl/pipeline.py` auto-discovers all `(ticker, interval)` combos under `data/spot/`, merges daily CSVs and monthly CSVs/ZIPs, deduplicates on `open_time`, and writes one `data/output/{TICKER}_{INTERVAL}.parquet` per combo (~40 files across 25 tickers). ZIPs are read in-memory; `.zip.*` partial-download files are purged first.
3. **Model**: Alpha model files load parquet via `pd.read_parquet`, compute indicators, and generate ±1 signals.

## Key Conventions

- Column names for kline data are normalised to snake_case via `utils.functions.lower_underscore` (strips non-alphanumeric, replaces spaces with `_`).
- `cudf` is used in `macd.py` alongside pandas — keep GPU/CPU dataframe usage explicit; do not mix them implicitly.
- Two WebSocket libraries coexist: `websockets` (async) and `websocket-client` (sync). `web_socket.py` uses both; prefer `websockets` for new async code.
- Altair visualisations require `alt.renderers.enable("browser")` and `alt.data_transformers.disable_max_rows()` before plotting.
