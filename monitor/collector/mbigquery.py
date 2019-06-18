from google.cloud import bigquery
import pandas as pd
import numpy as np
import time
class MBigquery(object):
    def __init__(self,dataset):
        self.client = bigquery.Client()
        self.dataset = dataset

    def insertData(self,table_id,data):
        dataset_id = self.dataset  # replace with your dataset ID
        table_id = table_id  # replace with your table ID
        table_ref = self.client.dataset(dataset_id).table(table_id)
        table = self.client.get_table(table_ref)  # API request
        errors = self.client.insert_rows(table, data)  # API request
        if errors != [] :
            return False
        return True

    # def getDepthPrice(self,exchange,symbol,time_start,time_end):
    #     sql = """
    #         SELECT bid1_price, ask1_price, time_int
    #         FROM `{}.{}`
    #         WHERE symbol = "{}" AND time_int>={} AND time_int<{}
    #         ORDER BY time_int ASC
    #     """
    #     sql = sql.format(self.dataset,exchange,symbol,time_start,time_end)
    #     df = self.client.query(sql).to_dataframe()
    #     df_time = pd.to_datetime(df['time_int'],unit='s')
    #     df = df.set_index(df_time)
    #     return df
    

    def query_depth_minute(self,exchange,symbol,time_start,time_end):
        sql = """
            SELECT bid1_price, ask1_price, time_int
            FROM `{dataset}.{exchange}`
            WHERE symbol = "{symbol}" AND time_int>={time_start} AND time_int < {time_end} 
            ORDER BY time_int ASC 
        """
        sql = sql.format(dataset=self.dataset,exchange=exchange,symbol=symbol,time_start=time_start,time_end=time_end)
        df = self.client.query(sql).to_dataframe()
        df_time = pd.to_datetime(df['time_int'],unit='s')
        df = df.set_index(df_time)
        return df
