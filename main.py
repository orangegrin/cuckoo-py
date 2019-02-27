#!/usr/bin/python3
exchangeA = "BitMex"
exchangeB = "HBHM"
symbol = "BTCUSD"
maxQty = 200
minRate = 0.003
Afees = -0.00025
Bfess = 0.00025
qtyRate = 0.3
market = {}


def subscribeorderbook(exchangeName, symbol, callback):
    NotImplementedError("subscribeorderbook")


def subscribeposition(exchangeName, symbol, callback):
    NotImplementedError("subscribeorderbook")


def subscribeorderchange(exchangeName, symbol, callback):
    NotImplementedError("subscribeorderbook")


# ====================handler===========================
def orderbookchangehandler(orderbook):
    position = market["position"]
    if(position.qty == 0):
        openposition(orderbook, "sell")
        openposition(orderbook, "buy")
    else:
        closeposition(orderbook, "sell")
        closeposition(orderbook, "buy")


def orderchangehandler(order):
    if(order.ordStatus == "Filled"):
        side = order.side == "buy" ? "sell": "buy"
        openmarketorder(exchangeB, symbol, side, order.qty)


def positionchangehandler(position)
    market["position"] = position

# =====================================================


def getlimitorderpair(orderbook, side):
    price = 0
    qty = 0
    fees = (Afees * orderbook.bid1.price) + (Bfess * orderbook.bid1.price)
    standarddev = getstandarddev(exchangeA, exchangeB, 'Min', 60)
    if(side == "sell"):
        price = orderbook.bid1.price * (minRate + 1) + fees * 2 + standarddev
        qty = orderbook.bid1.qty * qtyRate
    else
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


def openposition(orderbook, side):
    price, qty = getlimitorderpair(orderbook, side)
    if(qty > maxQty):
        qty = maxQty
    modifylimitorder(exchangeA, symbol, side, qty, price)


def closeposition(orderbook):
    position = market["position"]
    side = position.execQty > 0 ? "sell": "buy"
    price, qty = getlimitorderpair(orderbook, side)
    if(qty > position.qty)
        qty = position.qty
    modifylimitorder(exchangeA, symbol, side, qty, price)


def modifylimitorder(exchangeName, symbol, side, qty, price):
    NotImplementedError("openlimitorder")


def openmarketorder(exchangeName, symbol, side, qty):
    NotImplementedError("openmarketorder")


def getstandarddev(period, size):
    NotImplementedError("getstandarddev")


def run():
    subscribeorderbook(exchangeB, symbol, orderbookchangehandler)
    subscribeposition(exchangeB, symbol, positionchangehandler)
    subscribeorderchange(exchangeA, symbol, orderchangehandler)


run()
