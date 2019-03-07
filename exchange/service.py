import asyncio
import db.aredis as aredis
from db.redis_lib import RedisLib


class ExchangeService:
    def __init__(self):
        self.redislib = RedisLib()

    async def subscribe_orderbook(self, exchange_name, symbol, strategy_callback):
        channel = "OrderBookChange"+"."+exchange_name+"."+symbol
        channel = self.redislib.set_channel_name(channel)

        await self.subscribe(channel, callback=strategy_callback)

    def subscribe_position(self, exchange_name, symbol, callback):
        NotImplementedError("subscribeorderbook")

    def subscribe_order_change(self, exchange_name, symbol, callback):
        NotImplementedError("subscribeorderbook")

    def modify_limit_order(self, exchange_name, symbol, side, qty, price):
        NotImplementedError("openlimitorder")

    def open_market_order(self, exchange_name, symbol, side, qty):
        NotImplementedError("openmarketorder")

    # 获取平台标准价差
    def get_standard_dev(self, exchange_name_a, exchange_name_b, symbol_a, symbol_b, period, size):
        return 0
        # NotImplementedError("getstandarddev"

    def publish(self, channel, msg):
        NotImplementedError("getstandarddev")

    async def initexchange(self):
        self.redis = await aredis.create_redis('redis://localhost')

    async def subscribe(self, channel, callback):
        res = await self.redis.subscribe(channel)
        await asyncio.ensure_future(self.reader(res[0], callback))

    async def reader(self, ch, callback):
        while (await ch.wait_message()):
            print("on reader")
            data = await ch.get_json()
            # ch_name = ch.name.decode('utf-8')
            callback(data)
