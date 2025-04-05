from datetime import date, datetime

from settings.enums import Intervals, Months, Years


WHITELIST_CHARS = {letter: letter for letter in "abcdefghijklmnopqrstuvwxyz1234567890"}


DAILY_INTERVALS = [
    interval
    for interval in Intervals
    if interval.name
    in ["S1", "M1", "M3", "M5", "M15", "M30", "H1", "H2", "H4", "H6", "H8", "H12", "D1"]
]


PERIOD_START_DATE = "2020-01-01"
BASE_HISTORICAL_DATA_URL = "https://data.binance.vision/"
START_DATE = date(Years.Y2017, Months.JAN, 1)
END_DATE = datetime.date(datetime.now())
SYMBOLS = ["BTCUSDT"]


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
