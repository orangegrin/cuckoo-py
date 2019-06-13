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
log_manager = LogManager(base_log_path,'depth_minute')
# now = int(time.time())
# log_manager.save_log(now,'bitmex','testaa')
ws_obj = BinanceWs()
symbols = ['ethbtc','eosbtc','xrpbtc','adabtc','ltcbtc','trxbtc','bchabcbtc']
ws_obj.sub_depth(symbols)


last_save_time = 0
last_save_depth = {}
while True:
    symbols_depth = ws_obj.take_depth()
    for symbol in symbols_depth:
        item = symbols_depth[symbol]
        log_manager.check_save_minute('binance',symbol,item)
    time.sleep(1)