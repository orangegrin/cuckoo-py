import asyncio
import aioredis



class ExchangeService:
    def __init__(self,strategy):
        self.strategy = strategy

    async def subscribeorderbook(self,exchangeName, symbol, strategy_callback):
        channel = exchangeName+".orderbook"+"."+symbol
        await self.subscribe(channel, callback=self.onSubscribeOrderbook)

    def onSubscribeOrderbook(self, channel, data):
        print("on callback")
        print(channel)
        print(data)
        orderbook = [{1,2}]
        self.strategy.orderbookchangehandler(orderbook)

    def subscribeposition(self, exchangeName, symbol, callback):
        NotImplementedError("subscribeorderbook")


    def subscribeorderchange(self, exchangeName, symbol, callback):
        NotImplementedError("subscribeorderbook")


    def modifylimitorder(self, exchangeName, symbol, side, qty, price):
        NotImplementedError("openlimitorder")


    def openmarketorder(self, exchangeName, symbol, side, qty):
        NotImplementedError("openmarketorder")

    # 获取平台标准价差
    def GetStandardDev(exchangeNameA, exchangeNameB,symbol, period, size):
        return 0
        # NotImplementedError("getstandarddev")

        def getstandarddev(self, exchangeNameA, exchangeNameB, period, size):
            NotImplementedError("getstandarddev")

        def publish(self,channel,msg):
            NotImplementedError("getstandarddev")


        async def initexchange(self):
            self.redis = await aioredis.create_redis('redis://localhost')


        async def subscribe(self,channel,callback):
            res = await self.redis.subscribe(channel)
            await asyncio.ensure_future(self.reader(res[0],callback))

        async def reader(self, ch,callback):
            while (await ch.wait_message()):
                data = await ch.get_json()
                ch_name = ch.name.decode('utf-8')
                callback(ch_name,data)
