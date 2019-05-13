import redis
import requests
import traceback 
import time,datetime
import json
from decimal import Decimal 

redis_db = redis.Redis(host='localhost', port=6379, decode_responses=True)
Online_Diff_API = 'http://150.109.52.225:8888/diff?symbol={SYMBOL}&exchangeB=binance&exchangeA=bitmex'


def request_online_diff(symbol):
    try:
        resp = requests.get(Online_Diff_API.format(SYMBOL=symbol))
        # {"status":1,"msg":"success!","data":{"exchangepair":"bitmex\/binance","symbol":"ETH","timestamp":1557282780,"value":-0.0176779137}}
        resp.raise_for_status()
        if resp.json()["status"]==1:
            return resp.json()["data"]["value"]
        return None
    except Exception:
        print(traceback.format_exc())
        return None

def change_redis_diff_setting(redis_db_conn,redis_key,up_diff,down_diff):
    try:
        redis_dict = json.loads(redis_db_conn.get(redis_key))
        print("####################################################")
        print("old:")
        print(redis_dict)
        print("\n")
        # {"ExchangeNameA":"BitMEX","ExchangeNameB":"Binance","SymbolA":"EOSM19","SymbolB":"EOS_BTC","A2BDiff":-0.00553,"B2ADiff":-0.01253,"PerTrans":10.0,"MinPriceUnit":0.0000001,"CurAmount":404.0,"IntervalMillisecond":5000,"ProfitRange":0.003,"AutoCalcProfitRange":false,"AmountSymbol":"BTC","InitialExchangeBAmount":0.0,"FeesA":-0.0005,"FeesB":0.00075,"MaxAmount":1060.0,"EncryptedFileA":"BitMEX","EncryptedFileB":"Binance"}
        redis_dict["A2BDiff"] = up_diff
        redis_dict["B2ADiff"] = down_diff
        # redis_db_conn.set(redis_key,pretty_float_json_dumps(redis_dict)) 
        redis_dict_new = json.loads(redis_db_conn.get(redis_key))
        print("new:")
        # print(redis_dict_new)
        print(pretty_float_json_dumps(redis_dict))
        print("#####################################################\n")
        return True
    except Exception:
        print(traceback.format_exc())
        return None

def pretty_float_json_dumps(json_obj):

    dumps_str = ""
    if isinstance(json_obj, dict): 
        dumps_str += "{"
        for k,v in json_obj.items():
            dumps_str += json.dumps(k)+":"
            if isinstance(v, float): 
                float_tmp_str = ("%.16f" % v).rstrip("0")
                dumps_str += (float_tmp_str+'0' if float_tmp_str.endswith('.') else float_tmp_str) + ','
            elif isinstance(v, list) or isinstance(v, dict): 
                dumps_str += pretty_float_json_dumps(v)+','
            else:
                dumps_str += pretty_float_json_dumps(v)+','
        if dumps_str.endswith(','):
            dumps_str = dumps_str[:-1]
        dumps_str += "}"
    elif isinstance(json_obj, list): 
        dumps_str += "["
        for v in json_obj:
            if isinstance(v, float): 
                float_tmp_str = ("%.16f" % v).rstrip("0")
                dumps_str += (float_tmp_str+'0' if float_tmp_str.endswith('.') else float_tmp_str) + ','
            elif isinstance(v, list) or isinstance(v, dict): 
                dumps_str += pretty_float_json_dumps(v)+','
            else:
                dumps_str += pretty_float_json_dumps(v)+','
        if dumps_str.endswith(','):
            dumps_str = dumps_str[:-1]
        dumps_str += "]"
    elif isinstance(json_obj, float): 
        float_tmp_str = ("%.16f" % v).rstrip("0")
        dumps_str += (float_tmp_str+'0' if float_tmp_str.endswith('.') else float_tmp_str)
    else:
        dumps_str += json.dumps(json_obj)
    return dumps_str

if __name__ == "__main__":
    
    while True:
        
        eth_avg = request_online_diff("ETH")
        if type(eth_avg) is float:
            eth_avg = float(Decimal('%.5f' % eth_avg).quantize(Decimal('0.00000')))
            eth_updiff = eth_avg + 0.004
            eth_downdiff = eth_avg - 0.004
            if change_redis_diff_setting(redis_db,"INTERTEMPORAL:CONFIG:BitMEX:Binance:ETHM19:ETH_BTC:1",eth_updiff,eth_downdiff):
                print("Change eth success!!")
        
        eos_avg = request_online_diff("EOS")
        if type(eos_avg) is float:
            eos_avg = float(Decimal('%.5f' % eos_avg).quantize(Decimal('0.00000')))
            eos_updiff = eos_avg + 0.004
            eos_downdiff = eos_avg - 0.004
            if change_redis_diff_setting(redis_db,"INTERTEMPORAL:CONFIG:BitMEX:Binance:EOSM19:EOS_BTC:1",eos_updiff,eos_downdiff):
                print("Change eos success!!")
        
        print("--------------------------------------------------")
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("sleep 10 mins for next loop")
        print("--------------------------------------------------")
        time.sleep(60*10)
    