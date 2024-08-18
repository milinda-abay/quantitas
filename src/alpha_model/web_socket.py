import asyncio
import websockets
import json


async def hello():
    async with websockets.connect(
        "wss://data-stream.binance.vision:443/ws/btcusdt@kline_1s"
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
