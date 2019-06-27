from monitor.collector.log_manager import LogManager
import json
import time
import configparser
import logging
from exchange.bitmex.apihub.bitmex_websocket import BitMEXWebsocket



# config = configparser.ConfigParser()
# config.read('config.ini')

# api_key = config.get('bitmex','api_key')
# api_secret = config.get('bitmex','api_secret')

logger = logging.getLogger(__name__)

logger.setLevel(level=logging.INFO)
handler = logging.FileHandler('log/bitmex_collector.log')
formatter = logging.Formatter('%(asctime)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# now = int(time.time())
# log_manager.save_log(now,'bitmex','testaa')

# factory = BitmexWsFactory(None,None)
with open('collector.json','r') as load_f:
    collector_json = json.load(load_f)

symbols = collector_json['bitmex']['symbols']
# print(symbols)
base_log_path = 'collect_log'
log_manager = LogManager(base_log_path,collector_json['dataset'],'bitmex')


def make_connect(symbols):
    base_url = "wss://www.bitmex.com/realtime"
    bitmex_ws = BitMEXWebsocket(endpoint=base_url, symbol='XBTUSD',api_key=None,api_secret=None)
    bitmex_ws.sub_depth(symbols)
    return bitmex_ws


bitmex_obj = None
bitmex_obj = make_connect(symbols)
while True:
    # if not bitmex_ws.ws.sock or not bitmex_ws.ws.sock.connected :
    #     bitmex_ws.sub_depth(symbols)
    time_now = int(time.time())
    symbols_depth = bitmex_obj.take_depth()
    
    if time_now % 60 == 0:
        if bitmex_obj.ws.sock:
            bitmex_obj.logger.info("sock exist")
            if bitmex_obj.ws.sock.connected:
                bitmex_obj.logger.info("sock connect true")
        else:
            bitmex_obj = make_connect(symbols)
            symbols_depth = bitmex_obj.take_depth()
            
    for symbol in symbols_depth:
        item = symbols_depth[symbol]
        log_manager.check_save_minute('bitmex',symbol,item)
    
    time.sleep(1)

