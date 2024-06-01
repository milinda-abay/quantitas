from settings import INTERVALS, INPUT_PATH

import zipfile
import pandas as pd

BINANCE_BTC = INPUT_PATH / "btcusdt_binance"


files = BINANCE_BTC.glob("*")

for file in files:
    with zipfile.ZipFile(file, 'r') as zip_ref:
        zip_ref.extractall(BINANCE_BTC)

files = BINANCE_BTC.glob("*.csv")

x = list(files)[0]

'12h' in x.stem

for interval in INTERVALS:
    file_interval = (f for f in files if interval in f.stem )
    df = pd.concat(map(pd.read_csv, file_interval))

    

