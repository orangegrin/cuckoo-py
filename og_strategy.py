
from market_maker.bitmex_mon_api import  BitMexMon


def orderBookL2_data_format_func(data):
    print("In orderbookL2 data_format_func handle!!")
    return data[:6]+data[-6:]

def orderBookL2_callback(data):
    print("In orderbookL2 handle!!")
    print(data)

def run() -> None:
    bitmex_mon = BitMexMon('XBTUSD')

    # Try/except just keeps ctrl-c from printing an ugly stacktrace
    bitmex_mon.subscribe_data_callback('orderBookL2',orderBookL2_callback,orderBookL2_data_format_func)
    try:
        while True:
            sleep(3)
    except (KeyboardInterrupt, SystemExit):
        sys.exit()


if __name__ == "__main__":
    run()