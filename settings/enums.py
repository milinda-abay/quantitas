from enum import Enum


class Years(Enum):
    Y2017 = 2017
    Y2018 = 2018
    Y2019 = 2019
    Y2020 = 2020
    Y2021 = 2021
    Y2022 = 2022
    Y2023 = 2023
    Y2024 = 2024


class Intervals(Enum):
    S1 = "1s"
    M1 = "1m"
    M3 = "3m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H2 = "2h"
    H4 = "4h"
    H6 = "6h"
    H8 = "8h"
    H12 = "12h"
    D1 = "1d"
    D3 = "3d"
    W1 = "1w"
    MO1 = "1mo"


class Months(Enum):
    JAN = 1
    FEB = 2
    MAR = 3
    APR = 4
    MAY = 5
    JUN = 6
    JUL = 7
    AUG = 8
    SEP = 9
    OCT = 10
    NOV = 11
    DEC = 12


class TradingType(Enum):
    SPOT = "spot"
    UM = "um"
    CM = "cm"


class Trading_type(Enum):
    SPOT = "spot"
    UM = "um"
    CM = "cm"
