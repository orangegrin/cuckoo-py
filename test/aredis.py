import asyncio
import aioredis
import time

async def reader(ch):
    while (await ch.wait_message()):
        msg = await ch.get_json()
        ch_name = ch.name.decode('utf-8',msg)
        onSubscribe(ch_name,msg)

def onSubscribe(ch_name,msg):
    print(ch_name)
    print(msg)


# async def main():
#     sub = await aioredis.create_redis('redis://localhost')
#     channel = 'aa.bb.cc'
#     res = await sub.subscribe('aa.bb.cc')
#     await asyncio.ensure_future(reader(res[0]))


async def say_after(delay, what):
    await asyncio.sleep(delay)
    print(what)

async def main():
    redis_conn = await aioredis.create_redis('redis://localhost')
    channel1 = 'aa'
    channel2 = 'bb'

    res1 = await redis_conn.subscribe(channel1)
    res2 = await redis_conn.subscribe(channel2)

    task1 = asyncio.create_task(reader(res1[0]))
    task2 = asyncio.create_task(reader(res2[0]))

    # Wait until both tasks are completed (should take
    # around 2 seconds.)
    await task1
    await task2

asyncio.run(main())