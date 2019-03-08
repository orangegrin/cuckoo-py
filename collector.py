import threading
from huobi_ws import main as huobi_ws_main
from bitmex_ws_main import main as bitmex_ws_main
import time

huobi_ws_th = threading.Thread(target=huobi_ws_main, name='huobiThread')
bitmex_ws_th = threading.Thread(target=bitmex_ws_main, name='bitmexThread')
huobi_ws_th.start()
bitmex_ws_th.start()
huobi_ws_th.join()
bitmex_ws_th.join()


while True:
    time.sleep(1)