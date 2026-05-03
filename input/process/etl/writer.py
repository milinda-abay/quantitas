from pathlib import Path

import pandas as pd


class KlineWriter:
    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def write(self, df: pd.DataFrame, ticker: str, interval: str) -> Path:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_path(ticker, interval)
        df.to_parquet(path, index=False)
        return path

    def output_path(self, ticker: str, interval: str) -> Path:
        return self._output_dir / f"{ticker}_{interval}.parquet"
