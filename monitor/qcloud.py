import hashlib
import time
import requests
import json
import random

class Qcloud(object):
    def __init__(self,app_id,app_key):
        self.app_id = app_id
        self.app_key = app_key
        self.base_url = "https://cloud.tim.qq.com/v5/"

    def tpl_voice(self,tpl_id,params,mobile,nation_code="86",ext="",playtimes=3):
        rand_num = random.randint(1000000, 9999999)
        rand_num = str(rand_num)
        timestamp = int(time.time())
        signature = self.tls_sign(mobile,rand_num,timestamp)
        req_params = {
            "tpl_id": tpl_id,
            "params": params,
            "playtimes": playtimes,
            "sig": signature,
            "tel": {
                "mobile": mobile,
                "nationcode": nation_code
            },
            "time": timestamp,
            "ext": ext
        }
        path = "tlsvoicesvr/sendtvoice?sdkappid="+self.app_id+"&random="+rand_num
        ret = self._query('POST',path,req_params)
        return ret


    def voice(self,content,mobile,nation_code="86",ext="",playtimes=3):
        rand_num = random.randint(1000000, 9999999)
        rand_num = str(rand_num)
        timestamp = int(time.time())
        signature = self.tls_sign(mobile,rand_num,timestamp)
        req_params = {
            "promptfile": content,
            "prompttype": 2,
            "playtimes": playtimes,
            "sig": signature,
            "tel": {
                "mobile": mobile,
                "nationcode": nation_code
            },
            "time": timestamp,
            "ext": ext
        }
        path = "tlsvoicesvr/sendvoiceprompt?sdkappid="+self.app_id+"&random="+rand_num
        ret = self._query('POST',path,req_params)
        return ret




    def tls_sign(self,mobile,rand_num,timestamp):
        # 格式字符串
        fmt = "appkey={}&random={}&time={}&mobile={}"
        app_key = self.app_key
        encode_str = fmt.format(app_key, rand_num, timestamp, mobile)
        encode_str = bytes(encode_str, encoding = "utf8")

        # 计算sig
        sig = hashlib.sha256(encode_str).hexdigest()
        return sig
    
    
    def _query(self,method,path,params):
        query_url = self.base_url+path
        reqbody = json.dumps(params)
        res = requests.post(
            query_url,
            data=reqbody,
            )

        info = json.loads(res.content.decode())
        return info
    