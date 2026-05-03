import pandas as pd


class KlineTransformer:
    def __init__(self, dedup_col: str = "open_time") -> None:
        self._dedup_col = dedup_col

    def transform(self, frames: list[pd.DataFrame]) -> pd.DataFrame:
        if not frames:
            raise ValueError("No data frames to transform")
        df = pd.concat(frames, ignore_index=True)
        df = df.drop_duplicates(subset=[self._dedup_col], keep="first")
        df = df.sort_values(self._dedup_col, ascending=True)
        df = df.reset_index(drop=True)
        return df.convert_dtypes()
