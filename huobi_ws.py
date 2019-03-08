# -*- coding: utf-8 -*-
# import websockets
from websocket import create_connection
import gzip
import time
import json
import redis
import configparser
from db.redis_lib import RedisLib


def main():
    while(1):
        try:
            ws = create_connection("wss://www.hbdm.com/ws")
            break
        except:
            print('connect ws error,retry...')
            time.sleep(5)

    # 订阅 Market Depth 数据
    tradeStr_marketDepth = """
    {
        "sub": "market.BTC_CW.depth.step5", "id": "id1"
    }
    """

    config = configparser.ConfigParser()
    config.read('config.ini')
    rsLib = RedisLib()
    exchange = "huobi"
    symbol = "BTC_CW"

    redis_conn = redis.Redis(host='localhost', port=6379, db=0)

    ws.send(tradeStr_marketDepth)
    trade_id = ''
    price = 0
    while(1):
        compressData = ws.recv()
        result = gzip.decompress(compressData).decode('utf-8')
        if result[:7] == '{"ping"':
            ts = result[8:21]
            pong = '{"pong":'+ts+'}'
            print(pong)
            ws.send(pong)
            ws.send(tradeStr_marketDepth)

        else:
            # try:
            data = json.loads(result)
            if('tick' in data):
                if trade_id == data['tick']['id']:
                    continue
                else:
                    trade_id = data['tick']['id']
                    channel = rsLib.set_channel_name(
                        "OrderBookChange."+exchange+"."+symbol)
                    bids = rsLib.resample_orderbooks(
                        data['tick']['bids'], 0.5, False)
                    asks = rsLib.resample_orderbooks(
                        data['tick']['asks'], 0.5, True)

                    pubData = {
                        "Exchange": exchange,
                        "SequenceId":  data["tick"]["mrid"],
                        "MarketSymbol": symbol,
                        "LastUpdatedUtc": data["ts"],
                        "Asks": asks,
                        "Bids": bids
                    }
                    pubdata_json = json.dumps(pubData)
                    # print(pubdata_json)
                    # redis_conn.hmset(channel, {data['ts']: pubdata_json})
                    redis_conn.publish(channel, pubdata_json)
# if __name__ == '__main__':
#    while(1):
#        try:
#            ws = create_connection("wss://www.hbdm.com/ws")
#            break
#        except:
#            print('connect ws error,retry...')
#            time.sleep(5)

#    # 订阅 Market Depth 数据
#    tradeStr_marketDepth = """
#    {
#        "sub": "market.BTC_CW.depth.step5", "id": "id1"
#    }
#    """

#    config = configparser.ConfigParser()
#    config.read('config.ini')
#    rsLib = RedisLib()
#    exchange = "huobi"
#    symbol = "BTC_CW"

#    redis_conn = redis.Redis(host='localhost', port=6379)

#    ws.send(tradeStr_marketDepth)
#    trade_id = ''
#    price = 0
#    while(1):
#        compressData = ws.recv()
#        result = gzip.decompress(compressData).decode('utf-8')
#        if result[:7] == '{"ping"':
#            ts = result[8:21]
#            pong = '{"pong":'+ts+'}'
#            # print(pong)
#            ws.send(pong)
#            ws.send(tradeStr_marketDepth)

#        else:
#            # try:
#            data = json.loads(result)
#            if('tick' in data):
#                if trade_id == data['tick']['id']:
#                    continue
#                else:
#                    trade_id = data['tick']['id']
#                    channel = rsLib.set_channel_name(
#                        "OrderBookChange."+exchange+"."+symbol)
#                    bids = rsLib.resample_orderbooks(
#                        data['tick']['bids'], 0.5, False)
#                    asks = rsLib.resample_orderbooks(
#                        data['tick']['asks'], 0.5, True)

#                    pubData = {
#                        "Exchange": exchange,
#                        "SequenceId":  data["tick"]["mrid"],
#                        "MarketSymbol": symbol,
#                        "LastUpdatedUtc": data["ts"],
#                        "Asks": asks,
#                        "Bids": bids
#                    }
#                    pubdata_json = json.dumps(pubData)
#                    print(pubdata_json)
#                    res = redis_conn.publish(channel, pubdata_json)

#            # except Exception as e:
#            #     print(str(e))
