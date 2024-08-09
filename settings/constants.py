from datetime import date, datetime
from enum import Enum


WHITELIST_CHARS = {letter: letter for letter in "abcdefghijklmnopqrstuvwxyz1234567890"}

YEARS = ["2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024"]
INTERVALS = [
    "1s",
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "8h",
    "12h",
    "1d",
    "3d",
    "1w",
    "1mo",
]
DAILY_INTERVALS = [
    "1s",
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "8h",
    "12h",
    "1d",
]
MONTHS = list(range(1, 13))
PERIOD_START_DATE = "2020-01-01"
BASE_URL = "https://data.binance.vision/"
START_DATE = date(int(YEARS[0]), MONTHS[0], 1)
END_DATE = datetime.date(datetime.now())
SYMBOLS = ["BTCUSDT"]


class Trading_type(Enum):
    SPOT = "spot"
    UM = "um"
    CM = "cm"


KLINE_COL_NAMES = [
    "Open time",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "Close time",
    "Quote asset volume",
    "Number of trades",
    "Taker buy base asset volume",
    "Taker buy quote asset volume",
    "Ignore",
]
