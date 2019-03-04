# -*- coding: utf-8 -*-

from websocket import create_connection
import gzip
import time
import json

if __name__ == '__main__':
    while(1):
        try:
            ws = create_connection("wss://www.hbdm.com/ws")
            break
        except:
            print('connect ws error,retry...')
            time.sleep(5)

    # 订阅 Market Depth 数据
    tradeStr_marketDepth="""
    {
        "sub": "market.BTC_CW.depth.step5", "id": "id1"
    }
    """

    ws.send(tradeStr_marketDepth)
    trade_id = ''
    price = 0
    while(1):
        compressData=ws.recv()
        result=gzip.decompress(compressData).decode('utf-8')
        if result[:7] == '{"ping"':
            ts=result[8:21]
            pong='{"pong":'+ts+'}'
            # print(pong)
            ws.send(pong)
            ws.send(tradeStr_marketDepth)
            
        else:
            try:
                data = json.loads(result)
                if('tick' in data):
                    if trade_id == data['tick']['id']:
                        continue
                    else:
                        print(data)
                        trade_id = data['tick']['id']
            except Exception:
                pass

                # print(price)
                # price = 0
                # qty = 0
                # for i in range(0,5):
                #     orderprice = data['tick']['bids'][i]
                #     price = orderprice[0]
                #     qty += orderprice[1]
                # print('{},{}'.format(price, qty))
                # print(data['tick']['bids'])
