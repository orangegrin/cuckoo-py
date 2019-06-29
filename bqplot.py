from monitor.collector.mbigquery import MBigquery
import pandas as pd
import numpy as np
import time
from plotly.offline import plot
from plotly.graph_objs import Scatter, Box
import talib

dataset = "depth_minute"
exchange_a = "bitmex"
symbol_a = "EOSM19"

# exchange_a = "binance"
# symbol_a = "ethbtc"

exchange_b = "bitmex"
symbol_b = "XRPM19"

# exchange_b = "binance"
# symbol_b = "xrpbtc"

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
# diff_rate2 = diff_rate * 2


line_rate = Scatter(x=diff_rate.index, y=diff_rate.values, name="价差线")

ma1 = talib.MA(diff_rate,1440)
ma2 = talib.MA(diff_rate,1440*2)
ma3 = talib.MA(diff_rate,1440*3)
ma4 = talib.MA(diff_rate,1440*4)

line_ma1 = Scatter(x=ma1.index, y=ma1.values, name="ma1")
line_ma2 = Scatter(x=ma2.index, y=ma2.values, name="ma2")
line_ma3 = Scatter(x=ma3.index, y=ma3.values, name="ma3")
line_ma4 = Scatter(x=ma4.index, y=ma4.values, name="ma4")

plot_line = [
    line_rate,
    line_ma1,
    line_ma2,
    line_ma3,
    line_ma4
]

plot(plot_line, filename='./plothtml/plot-11.html')