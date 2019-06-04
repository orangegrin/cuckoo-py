from monitor.exchange.binance_ws import BinanceWs
from monitor.collector.log_manager import LogManager
import json
import time
import configparser
import logging


logger = logging.getLogger(__name__)

logger.setLevel(level=logging.INFO)
handler = logging.FileHandler('log/binance_collector.log')
formatter = logging.Formatter('%(asctime)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

base_log_path = 'collect_log'
log_manager = LogManager(base_log_path)
# now = int(time.time())
# log_manager.save_log(now,'bitmex','testaa')
ws_obj = BinanceWs()
symbols = ['ethbtc','eosbtc','xrpbtc','adabtc','ltcbtc','trxbtc','bchabcbtc']
ws_obj.sub_depth(symbols)
while True:
    symbols_depth = ws_obj.take_depth()
    for symbol in symbols_depth:
        item = symbols_depth[symbol]
        time_int = item['time_int']
        save_content = json.dumps(item)
        log_manager.save_log(time_int,'binance',save_content)
    time.sleep(1)

