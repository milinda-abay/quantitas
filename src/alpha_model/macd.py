from settings import DATA_PATH
import cudf 
import pandas as pd
import talib
from matplotlib import pyplot as plt

BTCUSDT_1M = DATA_PATH / "output" / "BTCUSDT_1m.parquet"

df = cudf.read_parquet(BTCUSDT_1M)

macd_fast,macd_slow,signal_period = 12,16,9

df['macd'],df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'].to_pandas(),macd_fast,macd_slow,signal_period )

df = df.reset_index(drop=True)

df.to_pandas()[['macd','macd_signal', 'macd_hist'] ].plot()
plt.show()

df.dtypes
df['open_time'] = df['open_time'] /1000
df['decimal'] = df.open_time.astype(int)

(df['open_time'] == df['decimal']).all()
