#!/usr/bin/python3
from bitmexom import bitmexom
import asyncio
import ExchangeService as es

exchangeA = "BitMex"
exchangeB = "HBHM"
symbol = "BTCUSD"
# 最大交易数量
maxQty = 200
# 平台最小价差率
minRate = 0.003
# A交易所限价单手续费
Afees = -0.00025
# B交易所市价手续费
Bfess = 0.00025
# 最大挂仓数量
qtyRate = 0.3
# 交易所数据信息
market = {}

# ====================handler===========================


def OrderbookChangeHandler(orderbook):
    position = market["position"]
    # 如果当前交易所有没有仓位
    if(position.qty == 0):

        # 双向开仓
        OpenPosition(orderbook, "sell")
        OpenPosition(orderbook, "buy")
    else:
       
        # 先平仓
        ClosePosition(orderbook)


def OrderChangeHandler(order):
    # 如果限价交易订单完成，则在另外一个交易所反向市价套保
    if(order.ordStatus == "Filled"):
        side = "sell" if order.side == "buy" else "buy"

        es.OpenMarketOrder(exchangeB, symbol, side, order.qty)


def PositionChangeHandler(position):
    # 保存仓位信息
    market["position"] = position


# 根据orderbook数据计算对手交易所的限价单开仓价格与数量
# orderbook.ask1 为最接近盘口的交易卖单
def GetLimitOrderPair(orderbook, side):
    price = 0
    qty = 0
    fees = (Afees * orderbook.bid1.price) + (Bfess * orderbook.bid1.price)
    standarddev = es.GetStandardDev(exchangeA,exchangeB,symbol,'Min',60)
    if(side == "sell"):
        price = orderbook.bid1.price * (minRate + 1) + fees * 2 + standarddev
        qty = orderbook.bid1.qty * qtyRate
    else:
        price = orderbook.ask1.price * (1 - minRate) - fees * 2 + standarddev
        qty = orderbook.ask1.qty * qtyRate
    return price, qty

# 根据orderbook计算计算对手交易所的限价平仓订单价格与数量
def GetClosePositionOrderPair(orderbook, side):
    price = 0
    qty = 0
    if(side == "sell"):
        price = orderbook.bid1.price
        qty = orderbook.bid1.qty * qtyRate
    else:
        price = orderbook.ask1.price
        qty = orderbook.ask1.qty * qtyRate
    return price, qty

# 根据orderbook数据进行开仓操作
def OpenPosition(orderbook, side):
    price, qty = GetLimitOrderPair(orderbook, side)
    if(qty > maxQty):
        qty = maxQty
    es.ModifyLimitOrder(exchangeA, symbol, side, qty, price)

# 根据orderbook数据进行平仓操作
def ClosePosition(orderbook):
    position = market["position"]
    side = "sell" if position.execQty > 0 else "buy"
    price, qty = GetClosePositionOrderPair(orderbook, side)
    if(qty > position.qty):
        qty = position.qty
    es.ModifyLimitOrder(exchangeA, symbol, side, qty, price)


async def Run():
    es.SubscribeOrderbook(exchangeB, symbol, 0.1, 200, OrderbookChangeHandler)
    es.SubscribePosition(exchangeA, symbol, PositionChangeHandler)
    es.SubscribeOrderChange(exchangeA, symbol, OrderChangeHandler)
