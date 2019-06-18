from monitor.collector.mbigquery import MBigquery
import pandas as pd
import numpy as np
import time
from plotly.offline import plot
from plotly.graph_objs import Scatter, Box


dataset = "depth_minute"
exchange_a = "bitmex"
symbol_a = "XBTM19"

exchange_b = "bitmex"
symbol_b = "XBTU19"


time_end = int(time.time())
time_start = time_end - 3600*24*30

mbq = MBigquery(dataset='depth_minute')

data_a = mbq.query_depth_minute(exchange=exchange_a,symbol=symbol_a,time_start=time_start,time_end=time_end)
data_b = mbq.query_depth_minute(exchange=exchange_b,symbol=symbol_b,time_start=time_start,time_end=time_end)

# series_a = pd.Series(data_a['ask1_price'],index=data_a['time_int'])
# series_b = pd.Series(data_b['bid1_price'],index=data_b['time_int'])
diff_num = data_b['bid1_price']-data_a['ask1_price']
diff_rate = diff_num/data_a['ask1_price']
# print(diff_rate.values)
# print(diff_rate)
diff_rate2 = diff_rate * 2


line1 = Scatter(x=diff_rate.index, y=diff_rate.values)
line2 = Scatter(x=diff_rate2.index, y=diff_rate2.values)
plot([line1,line2], filename='./plot-11.html')