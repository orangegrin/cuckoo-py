import asyncio
import aioredis


async def reader(ch):
    while (await ch.wait_message()):
        msg = await ch.get_json()
        ch_name = ch.name.decode('utf-8',msg)
        onSubscribe(ch_name,msg)

def onSubscribe(ch_name,msg):
    print(ch_name)
    print(msg)


async def main():
    sub = await aioredis.create_redis('redis://localhost')
    channel = 'aa.bb.cc'
    res = await sub.subscribe('aa.bb.cc')
    await asyncio.ensure_future(reader(res[0]))

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
