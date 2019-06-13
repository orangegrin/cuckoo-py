from google.cloud import bigquery
import pandas as pd
import numpy as np
client = bigquery.Client()
sql = """
    SELECT bid1_price as price, time_int
    FROM `test.bitmex`
    WHERE symbol = "ETHM19" 
    ORDER BY time_int ASC
"""

df = client.query(sql).to_dataframe()
df_time = pd.to_datetime(df['time_int'],unit='s')
df = df.set_index(df_time)
ts = pd.Series(df['price'],index=df_time)
ts = ts.resample('T').mean()



sql2 = """
    SELECT bid1_price as price, time_int
    FROM `test.binance`
    WHERE symbol = "ethbtc" 
    ORDER BY time_int ASC
"""

df2 = client.query(sql2).to_dataframe()
df_time2 = pd.to_datetime(df2['time_int'],unit='s')
df2 = df2.set_index(df_time2)
ts2 = pd.Series(df2['price'],index=df_time2)
ts2 = ts2.resample('T').mean()


ts3 = ts2/ts - 1
print(ts3)
# ser = pandas.Series(df['bid1_price'],index=df['time_int'])
# print(ser)
# # QUERY = "SELECT * FROM test.bitmex LIMIT 100"
# query_job = client.query(sql).to_dataframe()  # API request
# rows = query_job.result()  # Waits for query to finish
# for row in rows:
#     print(row.bid1_price)