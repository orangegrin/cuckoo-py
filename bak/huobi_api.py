from exchange.hbdm.api import HuobiAPI
from exchange.enums import Side

huobi = HuobiAPI()
market_symbol = "BTC_CW"
p_side = Side.Buy
amount = 300
ret = huobi.open_market_order('BTC',p_side,amount)
# ret = huobi.close_market_order('BTC',3,amount)
# print(ret)