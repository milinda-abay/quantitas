from settings import INTERVALS, INPUT_PATH

import zipfile
import pandas as pd

BINANCE_BTC = INPUT_PATH / "btcusdt_binance"


files = BINANCE_BTC.glob("*.zip")

for file in files:
    with zipfile.ZipFile(str(file), 'r') as zip_ref:
        zip_ref.extractall(BINANCE_BTC)

files = BINANCE_BTC.glob("*.csv")



for interval in INTERVALS:
    files = BINANCE_BTC.glob("*.csv")
    if interval in {"1s"}:
        continue
    file_interval = (f for f in files if interval in f.stem )
    df = pd.concat(map(pd.read_csv, file_interval))
    df.to_parquet(BINANCE_BTC / f"2024_{interval}.parquet")

    

