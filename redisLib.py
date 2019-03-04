import asyncio
import aioredis

class redisLib(object):
	def __init__(self, arg):
		super(redisLib, self).__init__()
		self.arg = arg
		
async def reader(ch):
    while (await ch.wait_message()):
        msg = await ch.get_json()
        print(ch)

def onSubscribe(ch,msg):
    print("")
