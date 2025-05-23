#!/usr/bin/env python

"""
  script to download klines.
  set the absolute path destination folder for STORE_DIRECTORY, and run

  e.g. STORE_DIRECTORY=/data/ ./download-kline.py

"""
import sys
from datetime import *
import pandas as pd
from settings.constants import *
from binance_public_data.utility import (
    download_file,
    get_all_symbols,
    get_parser,
    get_start_end_date_objects,
    convert_to_date_object,
    get_path,
)


def download_monthly_klines(
    trading_type,
    symbols,
    num_symbols,
    intervals,
    years,
    months,
    start_date,
    end_date,
    folder,
    checksum,
):
    date_range = start_date + " " + end_date if start_date and end_date else None
    start_date = convert_to_date_object(start_date) if start_date else START_DATE
    end_date = convert_to_date_object(end_date) if end_date else END_DATE
    print(f"Found {num_symbols} symbols")

    for current, symbol in enumerate(symbols):
        print(
            f"[{current + 1}/{num_symbols}] - start download monthly {symbol} klines "
        )
        for interval in intervals:
            for year in years:
                for month in months:
                    current_date = convert_to_date_object(f"{year}-{month}-01")
                    if current_date >= start_date and current_date <= end_date:
                        path = get_path(
                            trading_type, "klines", "monthly", symbol, interval
                        )
                        file_name = "{}-{}-{}-{}.zip".format(
                            symbol.upper(), interval, year, "{:02d}".format(month)
                        )
                        download_file(path, file_name, date_range, folder)

                        if checksum == 1:
                            checksum_path = get_path(
                                trading_type, "klines", "monthly", symbol, interval
                            )
                            checksum_file_name = "{}-{}-{}-{}.zip.CHECKSUM".format(
                                symbol.upper(), interval, year, "{:02d}".format(month)
                            )
                            download_file(
                                checksum_path, checksum_file_name, date_range, folder
                            )


def download_daily_klines(
    trading_type,
    symbols,
    num_symbols,
    intervals,
    dates,
    start_date,
    end_date,
    folder,
    checksum,
):
    date_range = start_date + " " + end_date if start_date and end_date else None
    start_date = convert_to_date_object(start_date) if start_date else START_DATE
    end_date = convert_to_date_object(end_date) if end_date else END_DATE
    # Get valid intervals for daily
    intervals = list(set(intervals) & set(DAILY_INTERVALS))
    print(f"Found {num_symbols} symbols")

    for current, symbol in enumerate(symbols):
        print(f"[{current + 1}/{num_symbols}] - start download daily {symbol} klines ")
        for interval in intervals:
            for date in dates:
                current_date = convert_to_date_object(date)
                if current_date >= start_date and current_date <= end_date:
                    path = get_path(trading_type, "klines", "daily", symbol, interval)
                    file_name = f"{symbol.upper()}-{interval}-{date}.zip"
                    download_file(path, file_name, date_range, folder)

                    if checksum == 1:
                        checksum_path = get_path(
                            trading_type, "klines", "daily", symbol, interval
                        )
                        checksum_file_name = (
                            f"{symbol.upper()}-{interval}-{date}.zip.CHECKSUM"
                        )
                        download_file(
                            checksum_path, checksum_file_name, date_range, folder
                        )


if __name__ == "__main__":
    parser = get_parser("klines")
    args = parser.parse_args(sys.argv[1:])

    if not args.symbols:
        print("fetching all symbols from exchange")
        symbols = get_all_symbols(args.type)
    else:
        symbols = args.symbols
    num_symbols = len(symbols)
    if args.dates:
        dates = args.dates
    else:
        period = convert_to_date_object(
            datetime.today().strftime("%Y-%m-%d")
        ) - convert_to_date_object(PERIOD_START_DATE)
        dates = (
            pd.date_range(end=datetime.today(), periods=period.days + 1)
            .to_pydatetime()
            .tolist()
        )
        dates = [date.strftime("%Y-%m-%d") for date in dates]
        if args.skip_monthly == 0:
            download_monthly_klines(
                args.type,
                symbols,
                num_symbols,
                args.intervals,
                args.years,
                args.months,
                args.startDate,
                args.endDate,
                args.folder,
                args.checksum,
            )
    if args.skip_daily == 0:
        download_daily_klines(
            args.type,
            symbols,
            num_symbols,
            args.intervals,
            dates,
            args.startDate,
            args.endDate,
            args.folder,
            args.checksum,
        )
