from monitor.exchange.bitmex_factory import BitmexWsFactory
from monitor.collector.log_manager import LogManager
import json
import time
import configparser
import logging


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

base_log_path = 'collect_log'
log_manager = LogManager(base_log_path)
# now = int(time.time())
# log_manager.save_log(now,'bitmex','testaa')

factory = BitmexWsFactory(None,None)
with open('collector.json','r') as load_f:
    collector_json = json.load(load_f)

symbols = collector_json['bitmex']['symbol']
print(symbols)

symbol_ws = {}
for sb in symbols:
    ws = factory.get_ws(sb)
    symbol_ws[sb] = {
        'ws':ws,
        'symbol':sb
    }

while True:
    for sb_obj in symbol_ws.values():
        ws = sb_obj['ws']
        depth = factory.market_depth(ws)
        symbol = depth['bids'][0]['symbol']
        time_int = depth['bids'][0]['time_int']
        time_ms = depth['bids'][0]['time_ms']
        save_data = {
            'symbol': symbol,
            'time_int': time_int,
            'time_ms': time_ms,
            'bid1_price': depth['bids'][0]['price'],
            'bid1_size': depth['bids'][0]['size'],

            'bid2_price': depth['bids'][1]['price'],
            'bid2_size': depth['bids'][1]['size'],

            'bid3_price': depth['bids'][2]['price'],
            'bid3_size': depth['bids'][2]['size'],

            'ask1_price': depth['asks'][0]['price'],
            'ask1_size': depth['asks'][0]['size'],

            'ask2_price': depth['asks'][1]['price'],
            'ask2_size': depth['asks'][1]['size'],

            'ask3_price': depth['asks'][2]['price'],
            'ask3_size': depth['asks'][2]['size'],
        }
        save_content = json.dumps(save_data)
        log_manager.save_log(time_int,'bitmex',save_content)
        print(time_ms)
    time.sleep(0.1)

