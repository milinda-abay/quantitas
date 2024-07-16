from settings import DAILY_KLINES, MONTHLY_KLINES, BASE_PATH, KLINE_COL_NAMES
from utils.functions import lower_underscore
import zipfile
import pandas as pd

from functools import partial

col_names = lower_underscore(KLINE_COL_NAMES)
read_csv = partial(pd.read_csv, names=col_names)


BTCUSDT_DAILY_1S = DAILY_KLINES / "BTCUSDT" / "1s"
BTCUSDT_MONTHLY_1S = MONTHLY_KLINES / "BTCUSDT" / "1s"

BTCUSDT_DAILY_1M = DAILY_KLINES / "BTCUSDT" / "1m"
BTCUSDT_MONTHLY_1M = MONTHLY_KLINES / "BTCUSDT" / "1m"


files = BTCUSDT_DAILY_1S.glob("*.csv")


pd.concat(map(pd.read_csv, files)).to_parquet(
    BASE_PATH / "data" / "output" / "BTCUSDT_1s.parquet"
)



files = BTCUSDT_MONTHLY_1M.glob("*.zip")

for file in files:
    with zipfile.ZipFile(str(file), 'r') as zip_ref:
        zip_ref.extractall(BTCUSDT_MONTHLY_1M)

files = BTCUSDT_MONTHLY_1M.glob("*.csv")

df = pd.concat(map(read_csv, files)).convert_dtypes()

df.to_parquet(
    BASE_PATH / "data" / "output" / "BTCUSDT_1m.parquet"
)

pd.read_parquet(BASE_PATH / "data" / "output" / "BTCUSDT_1m.parquet")


