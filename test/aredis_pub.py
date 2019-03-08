import asyncio
import aioredis


async def reader(ch):
    while (await ch.wait_message()):
        msg = await ch.get_json()
        print("Got Message:", msg)


async def main():
    pub = await aioredis.create_redis(
        'redis://localhost')

    res = await pub.publish_json('aa.bb.cc', "sfsd")
    # assert res == 1

    # await sub.unsubscribe('chan:1')
    # await tsk
    # sub.close()
    # pub.close()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())