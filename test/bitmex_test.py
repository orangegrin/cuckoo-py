import os.path, sys,time
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from exchange.bitmex.bitmex_mon_api import BitMexMon
from exchange import enums
if __name__ == "__main__":
    bitmexExchange = BitMexMon("XBTUSD",RestOnly=True)
    print(bitmexExchange.bitmex.http_open_orders(anyPrefix=True)) 
    time.sleep(1)
    bitmexExchange.converge_orders('XBTUSD',[],[{'price': 30000.0, 'orderQty': 100, 'side': enums.Side.Sell}])
    time.sleep(1)
    print(bitmexExchange.bitmex.http_open_orders(anyPrefix=True)) 
    time.sleep(1)
    # bitmexExchange.converge_orders('XBTUSD',[{'price': 3100.0, 'orderQty': 10, 'side': enums.Side.Buy}],[])
    time.sleep(1)
    