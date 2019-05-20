import json
import time
import configparser
import logging
from monitor.qcloud import Qcloud
import os
import errno
import sys
import time

class MonitorCuckoo(object):
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        app_id = config.get('qcloud','app_id')
        app_key = config.get('qcloud','app_key')
        self.qcloud_obj = Qcloud(app_id,app_key)
        self.config = config

        logger = logging.getLogger(__name__)

        logger.setLevel(level=logging.INFO)
        handler = logging.FileHandler('log/monitor.log')
        formatter = logging.Formatter('%(asctime)s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger
        self.warn_time = {}


    def send_voice(self,pid):
        # mobiles = [
        #     "15390099793", #jim
        #     "18011562820", #quiz
        #     "15680720878", #xinhang
        #     "18009082041", #tzq
        #     "18080818462", #xiaobo
        # ]

        monitor_config = self.get_monitor_config()
        mobiles = monitor_config['mobiles']
        enable_voice = monitor_config['enable_voice']
        pid = str(pid)
        for mb in mobiles:
            if enable_voice == True:
                ret = self.qcloud_obj.tpl_voice(329543,[pid],mb)
                ret_str = json.dumps(ret)
            else:
                ret_str = ""
            self.logger.info(mb+ " id:"+ pid + " " +ret_str)

    def check_proc(self,config):
        enable = config['enable']
        pid = config['pid']
        if enable == False:
            return True

        exist = self.check_pid(pid)

        if exist == True:
            return True

        progress_id = config['id']
        cur_time = time.time()

        time_check = self.warn_time_check(progress_id,cur_time)
        if time_check == True:
            self.send_voice(progress_id)
            return True
        return False
    

    # 返回 True 表示 需要 发送语音报警
    def warn_time_check(self,pid,cur_time):
        pid = str(pid)

        if pid not in self.warn_time:
            self.warn_time[pid] = {
                "time": cur_time
            }
            return True

        last_time  = self.warn_time[pid]['time']

        # 半小时重复报警
        if cur_time-last_time > 1800:
            self.warn_time[pid]['time'] = cur_time
            return True

        return False

    def check_pid(self,pid):
        """Check whether pid exists in the current process table.
        UNIX only.
        """
        if pid < 0:
            return False
        if pid == 0:
            # According to "man 2 kill" PID 0 refers to every process
            # in the process group of the calling process.
            # On certain systems 0 is a valid PID but we have no way
            # to know that in a portable fashion.
            raise ValueError('invalid PID 0')
        try:
            os.kill(pid, 0)
        except OSError as err:
            if err.errno == errno.ESRCH:
                # ESRCH == No such process
                return False
            elif err.errno == errno.EPERM:
                # EPERM clearly means there's a process to deny access to
                return True
            else:
                # According to "man 2 kill" possible error values are
                # (EINVAL, EPERM, ESRCH)
                raise
        else:
            return True
        

    def get_config(self):
        file = "../workspace/run.json"
        with open(file,'r') as load_f:
            config = json.load(load_f)
            return config

    def get_monitor_config(self):
        file = "monitor.json"
        with open(file,'r') as load_f:
            monitor_config = json.load(load_f)
            return monitor_config

    def run(self):
        config_json = self.get_config()
        for value in config_json.values():
            run_ret = self.check_proc(value)


cuckoo = MonitorCuckoo()
sleep_time = 60

while True:
   cuckoo.run()
   time.sleep(sleep_time)


