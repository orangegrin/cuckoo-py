import asyncio
import aioredis


class ExchangeService:

    async def subscribeorderbook(self, exchangeName, symbol, strategy_callback):
        channel = exchangeName+".orderbook"+"."+symbol
        await self.subscribe(channel, callback=strategy_callback)

    def subscribeposition(self, exchangeName, symbol, callback):
        NotImplementedError("subscribeorderbook")

    def subscribeorderchange(self, exchangeName, symbol, callback):
        NotImplementedError("subscribeorderbook")

    def ModifyLimitOrder(self, exchangeName, symbol, side, qty, price):
        NotImplementedError("openlimitorder")

    def OpenMarketOrder(self, exchangeName, symbol, side, qty):
        NotImplementedError("openmarketorder")

    # 获取平台标准价差
    def GetStandardDev(self, exchangeNameA, exchangeNameB, symbol, period, size):
        return 0
        # NotImplementedError("getstandarddev"

    def publish(self, channel, msg):
        NotImplementedError("getstandarddev")

    async def initexchange(self):
        self.redis = await aioredis.create_redis('redis://localhost')

    async def subscribe(self, channel, callback):
        res = await self.redis.subscribe(channel)
        await asyncio.ensure_future(self.reader(res[0], callback))

    async def reader(self, ch, callback):
        while (await ch.wait_message()):
            data = await ch.get_json()
            ch_name = ch.name.decode('utf-8')
            callback(data)
