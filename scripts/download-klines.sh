#!/bin/bash

# This is a simple script to download klines by given parameters.

symbols=("BTCUSDT") # add symbols here to download
intervals=("1m" "3m" "5m" "15m" "30m" "1h" "2h" "4h" "6h" "8h" "12h" "1d" "3d" "1w" "1mo") # add intervals here to download
years=("2020" "2021" "2022" "2023" "2024" "2025") # add years here to download
months=(01 02 03 04 05 06 07 08 09 10 11 12)

baseurl="https://data.binance.vision/data/spot/monthly/klines"

for symbol in "${symbols[@]}"; do
  for interval in "${intervals[@]}"; do
    for year in "${years[@]}"; do
      for month in "${months[@]}"; do
        url="${baseurl}/${symbol}/${interval}/${symbol}-${interval}-${year}-${month}.zip"
        save_dir="/workspaces/quantitas/data/spot/monthly/klines/${symbol}/${interval}"
        if wget --spider -q "${url}" 2>/dev/null; then
          wget -q --show-progress -P "${save_dir}" "${url}"
          echo "Downloaded: ${url}"
        else
          echo "File not found: ${url}"
        fi
      done
    done
  done
done