import requests
import traceback
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import json
# I = (Q - B) / T
# F = P + Clamp(I - P, -0.05%, 0.05%)

# B: https://www.bitmex.com/api/v1/trade?symbol=.XBTBON8H&reverse=true&count=1
# Q: https://www.bitmex.com/api/v1/trade?symbol=.USDBON8H&reverse=true&count=1
# P: https://www.bitmex.com/api/v1/trade?symbol=.XBTUSDPI8H&reverse=true&count=1
# [{"timestamp":"2019-05-29T04:00:00.000Z","symbol":".XBTBON8H","side":"Buy","size":0,"price":0.0003,"tickDirection":"ZeroMinusTick","trdMatchID":"00000000-0000-0000-0000-000000000000","grossValue":null,"homeNotional":null,"foreignNotional":null}]
# T: 3

def clamp(base_v,left_v=-0.0005,right_v=0.0005):
    if base_v < left_v:
        return left_v
    elif base_v > right_v:
        return right_v
    else:
        return base_v

def get_para_value(symbol,count=1):
    try:
        resp = requests.get("https://www.bitmex.com/api/v1/trade?symbol={SYMBOL}&reverse=true&count={COUNT}".format(SYMBOL=symbol,COUNT=str(count)))
        data = {}
        for item in resp.json():
            data[item['timestamp']] = item['price']
        return data
    except Exception:
        print(traceback.format_exc())
        return None

def calc_funding_rate(symbol):
    
    # I = (Q - B) / T
    # F = P + Clamp(I - P, -0.05%, 0.05%)
    Q_Data = get_para_value(".USDBON8H",30*3)
    B_Data = get_para_value(".{SYMBOL}BON8H".format(SYMBOL=symbol),30*3)
    P_Data = get_para_value(".{SYMBOL}USDPI8H".format(SYMBOL=symbol),30*3)
    final_data = {'timestamp':[],'fundingRate':[]}
    
    if Q_Data and B_Data and P_Data:
        for key in Q_Data.keys():
            I = (Q_Data[key] - B_Data[key]) / 3
            F = P_Data[key] + clamp(I-P_Data[key])
            final_data['timestamp'].append(key)
            final_data['fundingRate'].append(float('{:.8f}'.format(F)))
        df = pd.DataFrame({"fundingRate":final_data['fundingRate']},index=[ts.split(":")[0] for ts in final_data['timestamp']])
        
        
        df.to_csv('./funding_rate_log/{symbol}_fundingRate_{ts}.csv'.format(symbol=symbol,ts=datetime.now().strftime("%Y-%m-%dT%H0000")))
        # df.plot()
        # plt.show()
        return {'timestamp':final_data['timestamp'][0],'fundingRate':final_data['fundingRate'][0]}
    return None
def main():
    
    latest_value = {}
    xbt_fr = calc_funding_rate('XBT')
    if xbt_fr:
        latest_value['XBT'] = xbt_fr
    xbt_fr = calc_funding_rate('ETH')
    if xbt_fr:
        latest_value['ETH'] = xbt_fr
    if latest_value:
        with open('fundingRate.log','w') as fp:
            fp.write(json.dumps(latest_value))
    print(datetime.now().strftime("%Y-%m-%dT%H%M%S"))
    

if __name__ == "__main__":
    main()