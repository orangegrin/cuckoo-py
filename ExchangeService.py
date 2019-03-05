# 订阅交订单数据
def SubscribeOrderbook(exchangeName, symbol, depth, size, callback):
    NotImplementedError("subscribeorderbook")

# 订阅仓位数据
def SubscribePosition(exchangeName, symbol, callback):
    NotImplementedError("subscribeorderbook")

# 监听订单状态
def SubscribeOrderChange(exchangeName, symbol, callback):
    NotImplementedError("subscribeorderbook")

# 打开或/修改限价订单
def ModifyLimitOrder(exchangeName, symbol, side, qty, price):
    NotImplementedError("openlimitorder")

# 打开市价订单
def OpenMarketOrder(exchangeName, symbol, side, qty):
    NotImplementedError("openmarketorder")

# 获取平台标准价差
def GetStandardDev(exchangeNameA, exchangeNameB,symbol, period, size):
    return 0
    # NotImplementedError("getstandarddev")
