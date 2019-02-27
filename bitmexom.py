
from market_maker.market_maker import OrderManager
from market_maker.settings import settings
from market_maker.utils import log, constants, errors, math
import sys
import asyncio
import random


class bitmexom(OrderManager):
    async def run_loop(self):
        while True:
            sys.stdout.write("-----\n")
            sys.stdout.flush()
            self.check_file_change()
            await asyncio.sleep(settings.LOOP_INTERVAL)
            # This will restart on very short downtime, but if it's longer,
            # the MM will crash entirely as it is unable to connect to the WS on boot.
            if not self.check_connection():
                print("Realtime data connection unexpectedly closed, restarting.")
                self.restart()
            self.sanity_check()  # Ensures health of mm - several cut-out points here
            self.print_status()  # Print skew, delta, etc

    def place_orders(self):
        # """Create order items for use in convergence."""
        # buy_orders = []
        # sell_orders = []
        # rint = random.randint(0, 50)
        # buy_orders.append(
        #     {'price': 998.0 + rint, 'orderQty': 80+rint, 'side': "Buy"})
        # if(rint > 10):
        #     sell_orders.append(
        #         {'price': 10000.0 + rint, 'orderQty': 100 + rint, 'side': "Sell"})
        # return self.converge_orders(buy_orders, sell_orders)
        pass


# async def run():
#     om = bitmexom()
#     om.init()
#     await om.run_loop()

# async def main():
#     asyncio.create_task(run())
#     while True:
#         await asyncio.sleep(1)
#         print("===================================================")

# asyncio.run(main())