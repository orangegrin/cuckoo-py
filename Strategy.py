#!/usr/bin/python3
from bitmexom import bitmexom
import asyncio
import ExchangeService
from ExchangeService import ExchangeService

exchangeA = "bitmex"
exchangeB = "huobi"
symbol = "btc_usd"
maxQty = 200
minRate = 0.003
Afees = -0.00025
Bfess = 0.00025
qtyRate = 0.3
market = {}

# ====================handler===========================
class Strategy(object):
    """docstring for Stategy"""

    def orderbookchangehandler(self,orderbook):
        print(orderbook)
        # position = market["position"]
        # if(position.qty == 0):
        #     openposition(orderbook, "sell")
        #     openposition(orderbook, "buy")
        # else:
        #     closeposition(orderbook)


    def orderchangehandler(order):
        if(order.ordStatus == "Filled"):
            side = "sell" if order.side == "buy" else "buy"
            es.openmarketorder(exchangeB, symbol, side, order.qty)


    def positionchangehandler(position):
        market["position"] = position

    # =====================================================


    def getlimitorderpair(orderbook, side):
        price = 0
        qty = 0
        fees = (Afees * orderbook.bid1.price) + (Bfess * orderbook.bid1.price)
        standarddev = es.getstandarddev(exchangeA, exchangeB, 'Min', 60)
        if(side == "sell"):
            price = orderbook.bid1.price * (minRate + 1) + fees * 2 + standarddev
            qty = orderbook.bid1.qty * qtyRate
        else:
            price = orderbook.ask1.price * (1 - minRate) - fees * 2 + standarddev
            qty = orderbook.ask1.qty * qtyRate
        return price, qty


    def getclosepositionorderpair(orderbook, side):
        price = 0
        qty = 0
        if(side == "sell"):
            price = orderbook.bid1.price
            qty = orderbook.bid1.qty * qtyRate
        else:
            price = orderbook.ask1.price
            qty = orderbook.ask1.qty * qtyRate
        return price, qty


    def openposition(orderbook, side):
        price, qty = getlimitorderpair(orderbook, side)
        if(qty > maxQty):
            qty = maxQty
        es.modifylimitorder(exchangeA, symbol, side, qty, price)


    def closeposition(orderbook):
        position = market["position"]
        side = "sell" if position.execQty > 0 else "buy"
        price, qty = getclosepositionorderpair(orderbook, side)
        if(qty > position.qty):
            qty = position.qty
        es.modifylimitorder(exchangeA, symbol, side, qty, price)


async def run():
    strategy = Strategy()
    es = ExchangeService(strategy)
    await es.initexchange()
    await es.subscribeorderbook(exchangeB, symbol, strategy.orderbookchangehandler)
    # es.subscribeposition(exchangeA, symbol, positionchangehandler)
    # es.subscribeorderchange(exchangeA, symbol, orderchangehandler)
asyncio.get_event_loop().run_until_complete(run())