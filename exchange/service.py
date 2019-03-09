import asyncio
import aioredis
from db.redis_lib import RedisLib
from .bitmex.bitmex_mon_api import BitMexMon
from .hbdm.api import HuobiAPI
import time, threading
import traceback


class ExchangeService:
    def __init__(self):
        self.redislib = RedisLib()
        self.exchanges = {
            'bitmex':BitMexMon(symbol='XBTUSD',RestOnly=True),
            'huobi': HuobiAPI()
        }
        

    async def subscribe_orderbook(self, exchangename, symbol, callback):
        channel = "OrderBookChange"+"."+exchangename+"."+symbol
        res =  await self.subscribe(channel, callback=callback)
        task =  asyncio.create_task(self.reader(res[0], callback))
        return task

    async def subscribe_position(self, exchangename, symbol, callback):
        channel = "PositionChange"+"."+exchangename+"."+symbol
        res = await self.subscribe(channel, callback=callback)
        task =  asyncio.create_task(self.reader(res[0], callback))
        return task

    async def subscribe_order_change(self, exchangename, symbol, callback):
        channel = "OrderChange"+"."+exchangename+"."+symbol
        res = await self.subscribe(channel, callback=callback)
        task =  asyncio.create_task(self.reader(res[0], callback))
        return task

    def modify_limit_order(self, exchangename, symbol, side, qty, price):
        self.exchanges[exchangename].open_limit_order(symbol, side, qty, price)
        # NotImplementedError("openlimitorder")

    # buy_orders = []
    # sell_orders = []
    # populate buy and sell orders, e.g.
    # buy_orders.append({'price': 999.0, 'orderQty': 100, 'side': "Buy"})
    # sell_orders.append({'price': 1001.0, 'orderQty': 100, 'side': "Sell"})
    def converge_orders(self,exchangename,symbol,buy_orders, sell_orders):
        self.exchanges[exchangename].converge_orders(symbol,buy_orders, sell_orders)
        

    def open_market_order(self, exchangename, symbol, side, qty):
        self.exchanges[exchangename].open_market_order(symbol, side, qty)
        # NotImplementedError("openmarketorder")

    # 获取平台标准价差
    def get_standard_dev(self, exchangenamea, exchangenameb, symbola, symbolb, periodfreq, timeperiod):
        return 0
        # NotImplementedError("getstandarddev"

    def publish(self, channel, msg):
        NotImplementedError("getstandarddev")

    async def initexchange(self):
        self.redis = await aioredis.create_redis('redis://localhost')
        


    async def subscribe(self, channel, callback):
        channel = self.redislib.set_channel_name(channel)
        print("subscribe "+channel)
        res = await self.redis.subscribe(channel)
        # ch = self.reader(res[0])
        return res
        # task =  asyncio.create_task(self.reader(res[0], callback))
        # return task

    async def reader(self, ch, callback):
        while(await ch.wait_message()):
            data = await ch.get_json()
            ch_name = ch.name.decode('utf-8')
            print("on reader:"+ch_name)
            try:
                callback(data)
            except:
                traceback.print_exc()