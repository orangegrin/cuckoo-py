import json
import time
import configparser
import logging
from monitor.qcloud import Qcloud
import os
import errno
import sys

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


    def send_voice(self,pid):
        mobiles = [
            "15390099793", #jim
            "18011562820", #quiz
            "15680720878", #xinhang
            "18009082041", #tzq
            "18080818462", #xiaobo
        ]
        enable_voice = self.config.get('monitor','enable_voice')
        pid = str(pid)
        for mb in mobiles:
            if enable_voice == "1":
                ret = self.qcloud_obj.tpl_voice(329543,[pid],mb)
                ret_str = json.dumps(ret)
            else:
                ret_str = ""
            self.logger.info(mb+ " pid: "+ pid + " " +ret_str)

    def check_proc(self,config):
        enable = config['enable']
        pid = config['pid']
        if enable == False:
            return True

        exist = self.check_pid(pid)

        if exist == True:
            return True
        self.send_voice(config['id'])
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

    def run(self):
        config_json = self.get_config()
        for value in config_json.values():
            run_ret = self.check_proc(value)







cuckoo = MonitorCuckoo()
sleep_time = 60
cuckoo.run()

#while True:
#    cuckoo.run()
#    time.sleep(sleep_time)


# cuckoo.run()
