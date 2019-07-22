

import traceback,time
from sanic import Sanic
from sanic import response
import aiohttp
import json
import redis

from redis_utils import set_float_value_to_redis,get_float_value_from_redis,DIFF_OFFSET_KEY_DICT,PROFIT_RANGE_KEY_DICT

app = Sanic(__name__)


redis_db = redis.Redis(host='localhost', port=6379, decode_responses=True)

@app.route('/')
async def handle_request(request):
        return response.json({"msg":"Hello Sanic!"})



@app.route('/diff_offset',methods=['GET','POST','OPTIONS'])
def get_maavg_value_route(request):
    
    ret_data={}
    try:
        symbol_pair = request.raw_args["symbol_pair"] if request.raw_args.get("symbol_pair",None) else request.json["symbol_pair"]
        redis_key = DIFF_OFFSET_KEY_DICT.get(symbol_pair,None)
        if request.method=="GET":
            # symbol_pair = request.raw_args["symbol_pair"]
            # redis_key = DIFF_OFFSET_KEY_DICT.get(symbol_pair,None)
            ret_data = {"value":get_float_value_from_redis(redis_db,redis_key)}
        elif request.method=="POST":
            # symbol_pair = request.json["symbol_pair"]
            # redis_key = DIFF_OFFSET_KEY_DICT.get(symbol_pair,None)
            diff_offset_val = request.json["value"]
            set_float_value_to_redis(redis_db,redis_key,diff_offset_val)
            ret_data = {symbol_pair:diff_offset_val}
        print(request.json)
        
        return response.json(ret_data)
    except Exception:
        print(traceback.format_exc())
        return response.json(ret_data)

@app.route('/profit_range',methods=['GET','POST','OPTIONS'])
def get_profit_range_value_route(request):
    
    ret_data={}
    try:
        symbol_pair = request.raw_args["symbol_pair"] if request.raw_args.get("symbol_pair",None) else request.json["symbol_pair"]
        redis_key = PROFIT_RANGE_KEY_DICT.get(symbol_pair,None)
        if request.method=="GET":
            # symbol_pair = request.raw_args["symbol_pair"]
            # redis_key = PROFIT_RANGE_KEY_DICT.get(symbol_pair,None)
            ret_data = {"value":get_float_value_from_redis(redis_db,redis_key)}
        elif request.method=="POST":
            # symbol_pair = request.json["symbol_pair"]
            # redis_key = PROFIT_RANGE_KEY_DICT.get(symbol_pair,None)
            profit_range_val = request.json["value"]
            set_float_value_to_redis(redis_db,redis_key,profit_range_val)
            ret_data = {symbol_pair:profit_range_val}
        print(request.json)
        
        return response.json(ret_data)
    except Exception:
        print(traceback.format_exc())
        return response.json(ret_data)

@app.middleware('request')
async def print_on_request(request):
    if request.method == 'OPTIONS':
        return response.json(None)  

@app.middleware('response')
async def prevent_xss(request, response):
    if 'X-Error-Code' not in dict(response.headers):
        response.headers['X-Error-Code'] = 0
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT"
    response.headers["Access-Control-Allow-Headers"] = "X-Custom-Header,content-type"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8001, workers=1)