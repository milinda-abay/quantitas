from settings import DATA_PATH
import pandas as pd
import talib
from matplotlib import pyplot as plt

BTCUSDT_1M = DATA_PATH / "output" / "BTCUSDT_1m.parquet"

df = pd.read_parquet(BTCUSDT_1M)


df['macd'],df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'])

df[['macd','macd_signal', 'macd_hist'] ]
fig = plt.figure()
fig.show()