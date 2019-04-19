
from twisted.internet import reactor
from binance.websockets import BinanceSocketManager
from binance.depthcache import DepthCacheManager
from binance.client import Client
import datetime,pprint,time
from collections import OrderedDict
SYMBOL_MAP={
    "ETHBTC":"ETH/BTC",
    "EOSBTC":"EOS/BTC",
    "LTCBTC":"LTC/BTC",
    "XRPBTC":"XRP/BTC"
}
GSYMBOL_BINANCE={
     "ETH/BTC":"ETHBTC",
    "EOS/BTC":"EOSBTC",
    "LTC/BTC":"LTCBTC",
    "XRP/BTC":"XRPBTC"
}

class BinanceDataAPI():

    def __init__(self,symbols=["ETH/BTC"],eventCallbacks={"depth": lambda x : print(x)},api_key="",api_secret=""):
        self.data_cache={}
        self.symbols = [GSYMBOL_BINANCE[s] for s in symbols]
        self.client = Client(api_key, api_secret)
        self.bm = BinanceSocketManager(self.client)
        self.eventsymbols = list(eventCallbacks.keys())
        self.eventCallbacks = eventCallbacks
        self.init_data()

    def update_askbid(self,symbol,bidask,ulist,reverse=False):
        self.data_cache.setdefault(symbol,{})
        self.data_cache[symbol].setdefault(bidask,{})
        ulist_dict = {float(pa[0]):float(pa[1]) for pa in ulist }
        old_dict = self.data_cache[symbol][bidask]
        old_dict.update(ulist_dict)
        old_dict = { k:v for k,v in old_dict.items() if v != 0.0}
        keys  = sorted(old_dict.keys(), reverse=reverse)
        orderdict = OrderedDict({})
        for k in keys:
            orderdict[k]=old_dict[k]
        self.data_cache[symbol][bidask] = orderdict

    def process_m_message(self,msg):
        # print("stream: {} data: {}".format(msg['stream'], msg['data']))
        # for eventsymbol in self.eventsymbols:
        #     if msg['data']['e'].find(eventsymbol.lower()) >=0:
        #         self.eventCallbacks[eventsymbol](msg)
        timestamp = datetime.datetime.fromtimestamp(msg['data']['E']/1000).strftime("%Y-%m-%dT%H:%M:%S")
        symbol = SYMBOL_MAP[msg['data']['s']]
        self.update_askbid(symbol,'asks',msg['data']['a'],reverse=True) 
        self.update_askbid(symbol,'bids',msg['data']['b'],reverse=False)
        print(timestamp,symbol,self.data_cache[symbol]['bids'].popitem(),self.data_cache[symbol]['asks'].popitem())
        lastask = self.data_cache[symbol]['asks'].popitem()
        lastbid = self.data_cache[symbol]['bids'].popitem()
        self.data_cache[symbol]['asks'][lastask[0]]=lastask[1]
        self.data_cache[symbol]['bids'][lastbid[0]]=lastbid[1]
        sd = {
            'asks':lastask[0],
            'bids':lastbid[0],
            'symbol':symbol,
            'exchange':'binance',
            'timestamp':timestamp
        }
        for eventsymbol in self.eventsymbols:
            if msg['data']['e'].find(eventsymbol.lower()) >=0:
                self.eventCallbacks[eventsymbol](sd)

    
    def init_data(self):
        client = Client("api_key", "api_secret")
        for symbol in self.symbols:#,'EOSBTC','XRPBTC','LTCBTC'
            depth_cache = client.get_order_book(symbol= symbol)
            print(depth_cache)
            
            self.update_askbid(SYMBOL_MAP[symbol],'asks',depth_cache["asks"],reverse=True)
            self.update_askbid(SYMBOL_MAP[symbol],'bids',depth_cache["bids"],reverse=False)  

            print("sss")       
    
    def start(self):
        self.bm.start_multiplex_socket(['{coin}@{event}'.format(coin=coinsymbol.lower(),event=eventsymbol.lower()) for eventsymbol in self.eventsymbols for coinsymbol in self.symbols], self.process_m_message)

    def close(self):
        print("close....")
        self.bm.close()
        reactor.stop()
        print("finished....")


if __name__ == "__main__":

    bda = BinanceDataAPI()
    try:
        bda.start()
        while True:
            time.sleep(10)
            
    except Exception as e:
        print("-----------------------")
    finally:
        bda.close()
    
    
        
# {'e': 'depthUpdate', 'E': 1555039849238, 's': 'ETHBTC', 'U': 3256100', '56.81600000'], ['0.03255700', '29.52200000'], ['0.03255200', '0.27900000'], [000', '30.82100000'], ['0.03248200', '0.00000000']], 'a': [['0.03258200', '53.30200000']262500', '6.77100000']]}