import json
import time
import configparser
import logging
import os
import errno
import sys
import time

class LogManager(object):
    def __init__(self,base_log_path):
        self.base_log_path = base_log_path
        self.file_handler = {}

    def save_log(self,time_int,exchange_name,content):
        time_log = time_int - time_int % 3600
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

        # self.checkHandler()

    # def checkHandler(self):
    #     now = int(time.time())
    #     for file in self.file_handler.values():
    #         if now - file['time'] > 3600:
    #             file_handler.pop(file, None)