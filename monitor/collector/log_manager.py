import json
import time
import configparser
import logging
import os
import errno
import sys
import time
from monitor.collector.mbigquery import MBigquery

class LogManager(object):
    def __init__(self,base_log_path,bq_dataset):
        self.base_log_path = base_log_path
        self.file_handler = {}
        self.minute_data = {}
        self.bigquery = MBigquery(bq_dataset)




        logger = logging.getLogger(__name__)

        logger.setLevel(level=logging.INFO)
        handler = logging.FileHandler('log/binance_collector.log')
        formatter = logging.Formatter('%(asctime)s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger

    def save_log(self,time_int,exchange_name,content):
        time_log = time_int - time_int % (3600*24)
        time_log = str(time_log)
        folder = self.base_log_path + "/"+time_log
        folder_exist = os.path.exists(folder)

        if not folder_exist:
            os.makedirs(folder)
        now = int(time.time())

        file = folder +"/"+exchange_name + "-"+time_log
        # if file not in self.file_handler:
        #     fd = open(file,'a')
        #     self.file_handler[file] = {
        #         'fd':fd,
        #         'time':now
        #     }
        # fd = self.file_handler[file]['fd']

        fd = open(file,'a')
        fd.write(content+"\n")
        fd.close()

    def save_minute(self,exchange,symbol,minute_time,data):
        new_data = {}
        new_data['bid1_price'] = self.get_average(data,'bid1_price')
        new_data['bid2_price'] = self.get_average(data,'bid2_price')
        new_data['bid3_price'] = self.get_average(data,'bid3_price')
        new_data['bid1_size'] = int(self.get_average(data,'bid1_size'))
        new_data['bid2_size'] = int(self.get_average(data,'bid2_size'))
        new_data['bid3_size'] = int(self.get_average(data,'bid3_size'))
        new_data['ask1_price'] = self.get_average(data,'ask1_price')
        new_data['ask2_price'] = self.get_average(data,'ask2_price')
        new_data['ask3_price'] = self.get_average(data,'ask3_price')
        new_data['ask1_size'] = int(self.get_average(data,'ask1_size'))
        new_data['ask2_size'] = int(self.get_average(data,'ask2_size'))
        new_data['ask3_size'] = int(self.get_average(data,'ask3_size'))
        insert_data = [
            (
                symbol,
                minute_time,
                new_data['bid1_price'],
                new_data['bid1_size'],
                new_data['bid2_price'],
                new_data['bid2_size'],
                new_data['bid3_price'],
                new_data['bid3_size'],
                new_data['ask1_price'],
                new_data['ask1_size'],
                new_data['ask2_price'],
                new_data['ask2_size'],
                new_data['ask3_price'],
                new_data['ask3_size']
            )
        ]
        ret = self.bigquery.insertData(exchange,insert_data)
        content = json.dumps(insert_data)
        print(content)
        self.logger.info('save data : '+content)


    def get_average(self,data,field):
        num = 0
        length = 0
        numeric = -1
        for item in data:
            if field not in item:
                continue
            
            x = item[field].split('.',1)
            numeric2 = len(x[1])
            if numeric2 > numeric:
                numeric = numeric2
                
            num += float(item[field])
            length += 1

        if length == 0:
            return 0
        average = num/length
        average = round(average,numeric)
        return average

    def check_save_minute(self,exchange,symbol,data):
        now = int(time.time())
        minute_time = now-now%10
        if symbol in self.minute_data:
            last_time = self.minute_data[symbol]['last_time']
            last_data = self.minute_data[symbol]['last_data']
        else :
            last_data = [data]
            last_time = minute_time
            self.minute_data[symbol] = {
                'last_time': minute_time,
                'last_data':last_data
            }
            return True
        
        if minute_time > last_time:
            self.save_minute(exchange,symbol,minute_time,self.minute_data[symbol]['last_data'])
            self.minute_data[symbol]['last_time'] = minute_time
            self.minute_data[symbol]['last_data'] = []
            return True
        else:
            self.minute_data[symbol]['last_data'].append(data)
            return True

        # self.checkHandler()

    # def checkHandler(self):
    #     now = int(time.time())
    #     for file in self.file_handler.values():
    #         if now - file['time'] > 3600:
    #             file_handler.pop(file, None)