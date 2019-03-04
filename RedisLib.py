import configparser


class RedisLib(object):
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.env =  self.config.get('env','env')

    def setChannelName(self, channel):
        newChannel = self.env +"."+ channel
        return newChannel