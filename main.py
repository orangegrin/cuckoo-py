#!/usr/bin/python3
import asyncio
from exchange.service import ExchangeService
from exchange.enums import Side
from exchange.enums import OrderType
from exchange.enums import OrderResultType

import time
import threading
from huobi_ws import main as huobi_ws_main
from bitmex_ws_main import main as bitmex_ws_main
exchange_a = "bitmex"
exchange_b = "huobi"
symbol_a = "BTC_USD"
symbol_b = "BTC_CW"
max_qty = 10
min_rate = 0.003
a_fees = -0.00025
b_fess = 0.00025
qty_rate = 0.3
market = {}
# ====================handler===========================


class Strategy(object):
    def __init__(self):
        es = ExchangeService()
        self.es = es

    def orderbook_change_handler(self, orderbook):
        position = market["position"]
        # 如果当前交易所有没有仓位
        if(position != None and position.qty == 0):
            print("准备双向开仓")
            # 双向开仓
            self.open_position(orderbook, Side.Buy)
            self.open_position(orderbook, Side.Sell)
        else:
            print("准备平仓")
            # 先平仓
            self.close_position(orderbook)

    def order_change_handler(self, order_request):
        """order_request: ExchangeOrderRequest"""
        # 如果限价交易订单完成，则在另外一个交易所反向市价套保
        #print("exchangeA 挂单交易成功")
        if(order_request.orderType == OrderResultType.Filled):
            side = Side.Sell if order_request.side == Side.Buy else Side.Buy
            self.es.open_market_order(
                exchange_b, symbol_b, side, order_request.qty)

    def position_change_handler(self, position):
        # 保存仓位信息
        print("刷新仓位数据")
        market["position"] = position

    def get_limit_order_pair(self, orderbook, side):
        """
            # =====================================================
            # 根据orderbook数据计算对手交易所的限价单开仓价格与数量
            # orderbook.bid1 为最接近盘口的交易买单
            # orderbook.ask1 为最接近盘口的交易卖单
        """
        price = 0
        qty = 0
        fees = (a_fees * orderbook.bids[0].price) + \
            (b_fess * orderbook.bids[0].price)
        # standarddev = symbol_a- exchange_b
        standarddev = self.es.get_standard_dev(
            exchange_a, exchange_b, symbol_a, symbol_b, "Min", 60)

        if(side == Side.Sell):
            price = orderbook.bids[0].price * \
                (min_rate + 1) + fees * 2 + standarddev
            qty = orderbook.bids[0].qty * qty_rate
        else:
            price = orderbook.asks[0].price * \
                (1 - min_rate) - fees * 2 + standarddev
            qty = orderbook.asks[0].qty * qty_rate
        return price, qty

    # 根据orderbook计算计算对手交易所的限价平仓订单价格与数量
    def get_close_position_order_pair(self, orderbook, side):
        price = 0
        qty = 0
        if(side == Side.Sell):
            price = orderbook.bids[0].price
            qty = orderbook.bids[0].qty * qty_rate
        else:
            price = orderbook.asks[0].price
            qty = orderbook.asks[0].qty * qty_rate
        return price, qty

    # 根据orderbook数据进行开仓操作
    def open_position(self, orderbook, side):
        price, qty = self.get_limit_order_pair(orderbook, side)
        if(qty > max_qty):
            qty = max_qty
        print("执行开仓 Side:"+side.value+" qty:"+qty+" price"+price)
        self.es.modify_limit_order(exchange_a, symbol_a, side, qty, price)

    # 根据orderbook数据进行平仓操作
    def close_position(self, orderbook):
        position = market["position"]
        side = Side.Sell if position.qty > 0 else Side.Buy
        price, qty = self.get_close_position_order_pair(orderbook, side)
        if(qty > position.qty):
            qty = position.qty
        print("执行平仓 Side:"+side.value+" qty:"+qty+" price"+price)
        self.es.modify_limit_order(exchange_a, symbol_a, side, qty, price)

    async def run(self):
        # await self.es.initexchange()
        # asyncio.create_task(self.es.subscribe_orderbook(exchange_b, symbol_b, self.orderbook_change_handler))
        # asyncio.create_task(self.es.subscribe_position(exchange_a, symbol_a, self.position_change_handler))
        # asyncio.create_task(self.es.subscribe_order_change(exchange_a, symbol_a, self.order_change_handler))
        while True:
            await asyncio.sleep(1)


async def run():
    strategy = Strategy()
    await strategy.run()

huobi_ws_th = threading.Thread(target=huobi_ws_main, name='huobiThread')
bitmex_ws_th = threading.Thread(target=bitmex_ws_main, name='bitmexThread')
huobi_ws_th.start()
bitmex_ws_th.start()
huobi_ws_th.join()
bitmex_ws_th.join()
asyncio.run(run())

# huobi_ws_main()
# bitmex_ws_main()
