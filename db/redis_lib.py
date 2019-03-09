import configparser
import numpy as np
import pandas as pd
import json
class RedisLib(object):
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.env = self.config.get('env', 'env')

    def set_channel_name(self, channel):
        new_channel = self.env + "." + channel
        print(new_channel)
        return new_channel

    def setKeyName(self, name):
        new_name = self.env + "." + name
        return new_name

    # ascending 为True 为从小到大
    def resample_orderbooks(self,pricePairs, samplingRate, ascending):
        ary = np.array(pricePairs).T
        prices = ary[0]
        qtys = ary[1]
        d2 = dict({'qty': qtys})
        df = pd.DataFrame(d2, index=pd.to_timedelta(prices, unit='S'))
        df = df.resample(str(samplingRate)+'S').sum()
        pricesB = df.index.microseconds / 1000 / 1000 + \
            df.index.seconds + df.index.nanoseconds / 1000/1000 / 1000
        df.index = pricesB
        res = df[df['qty'] > 0]
        res = res.sort_index(ascending=ascending)
        prices = np.array([res.index,res['qty']]).T.tolist()
        return prices