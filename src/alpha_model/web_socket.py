import asyncio
import websockets  # this is async websockets library
import websocket  # this is websocket-client library
import json


async def hello():
    async with websockets.connect(
        "wss://data-stream.binance.vision:443/ws/ethusdt@kline_1m"
    ) as ws:
        while True:
            response = await asyncio.wait_for(ws.recv(), timeout=2)
            response = json.loads(response)
            print(response)
            await asyncio.sleep(0.5)


asyncio.get_event_loop().run_until_complete(hello())


# btcusdt@aggTrade
# ethusdt@ticker
# ethusdt@kline_1m
# !ticker@arr
# !miniTicker@arr
# "wss://stream.binance.com:9443/stream?streams=btcusdt@aggTrade/!miniTicker@arr/ethusdt@ticker"
# "wss://data-stream.binance.vision/ws/!ticker@arr"


symbol = "btcusdt"
socket = f"wss://data-stream.binance.vision:443/ws/{symbol}@trade"
socket = "wss://data-stream.binance.vision/ws/!ticker@arr"


def on_message(ws, message):
    print(message)


def on_error(ws, error):
    print(error)


def on_close(ws, close_status_code, close_msg):
    print("### closed ###")


def on_open(ws):
    print("### connected ###")


ws = websocket.WebSocketApp(
    socket, on_message=on_message, on_error=on_error, on_close=on_close
)

ws.run_forever()


import pandas as pd


pd.to_datetime(1724073560302000000)