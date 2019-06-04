import websocket
import threading
import traceback
from time import sleep
import json
import logging
import urllib
import math

# Naive implementation of connecting to BitMEX websocket for streaming realtime data.
# The Marketmaker still interacts with this as if it were a REST Endpoint, but now it can get
# much more realtime data without polling the hell out of the API.
#
# The Websocket offers a bunch of data as raw properties right on the object.
# On connect, it synchronously asks for a push of all this data then returns.
# Right after, the MM can start using its data. It will be updated in realtime, so the MM can
# poll really often if it wants.
class BinanceWs:

    # Don't grow a table larger than this amount. Helps cap memory usage.
    MAX_TABLE_LEN = 200

    def __init__(self, api_key=None, api_secret=None):
        '''Connect to the websocket and initialize data stores.'''
        self.logger = logging.getLogger(__name__)
        
        handler = logging.FileHandler('log/binance_ws.log')
        formatter = logging.Formatter('%(asctime)s %(message)s')
        handler.setFormatter(formatter)
        self.logger.setLevel(level=logging.INFO)
        self.logger.addHandler(handler)
        self.endpoint = "wss://stream.binance.com:9443"

        self.logger.debug("Initializing WebSocket.")

        if api_key is not None and api_secret is None:
            raise ValueError('api_secret is required if api_key is provided')
        if api_key is None and api_secret is not None:
            raise ValueError('api_key is required if api_secret is provided')

        self.api_key = api_key
        self.api_secret = api_secret

        self.data = {}
        self.keys = {}
        self.exited = False

        # We can subscribe right in the connection querystring, so let's build that.
        # Subscribe to all pertinent endpoints
        # wsURL = self.__get_url()
        # self.logger.info("Connecting to %s" % wsURL)
        self.logger.info('Connected to WS.')

        # Connected. Wait for partials
        # self.__wait_for_symbol(symbol)
        # if api_key:
        #     self.__wait_for_account()
        # self.logger.info('Got all market data. Starting.')

    def exit(self):
        '''Call this to exit - will close websocket.'''
        self.exited = True
        self.ws.close()

    # def get_instrument(self):
    #     '''Get the raw instrument data for this symbol.'''
    #     # Turn the 'tickSize' into 'tickLog' for use in rounding
    #     instrument = self.data['instrument'][0]
    #     instrument['tickLog'] = int(math.fabs(math.log10(instrument['tickSize'])))
    #     return instrument

    # def get_ticker(self):
    #     '''Return a ticker object. Generated from quote and trade.'''
    #     lastQuote = self.data['quote'][-1]
    #     lastTrade = self.data['trade'][-1]
    #     ticker = {
    #         "last": lastTrade['price'],
    #         "buy": lastQuote['bidPrice'],
    #         "sell": lastQuote['askPrice'],
    #         "mid": (float(lastQuote['bidPrice'] or 0) + float(lastQuote['askPrice'] or 0)) / 2
    #     }

    #     # The instrument has a tickSize. Use it to round values.
    #     instrument = self.data['instrument'][0]
    #     return {k: round(float(v or 0), instrument['tickLog']) for k, v in ticker.items()}

    # def funds(self):
    #     '''Get your margin details.'''
    #     return self.data['margin'][0]

    # def positions(self):
    #     '''Get your positions.'''
    #     return self.data['position']

    def sub_depth(self,symbols):
        path = "/stream?streams="
        for symbol in symbols:
            path += symbol+"@depth/"
        path = path[0:-1]
        self.connect(path,self.on_depth)

    def on_depth(self,message):
        message = json.loads(message)
        symbol = message['data']['s']
        symbol = symbol.lower()
        self.data[symbol] = message['data']
        
        # if 'orderBookL2_25' in self.data:
        #     return self.data['orderBookL2_25']
        # else:
        #     return None
    def take_depth(self):
        ret_data = {}
        for symbol in self.data:
            item = self.data[symbol]
            time_int = int(item['E']/1000)
            bid_depth_len = len(item['b'])
            ask_depth_len = len(item['a'])
            if bid_depth_len < 1 or ask_depth_len < 1:
                continue

            symbol_depth = {
                'time_int': time_int,
                'symbol': symbol,
                'bid1_price': item['b'][0][0],
                'bid1_size': item['b'][0][1],

                'ask1_price': item['a'][0][0],
                'ask1_size': item['a'][0][1],
            }

            if bid_depth_len >=2 :
                symbol_depth['bid2_price'] = item['b'][1][0]
                symbol_depth['bid2_size'] = item['b'][1][1]

            if bid_depth_len >=3 :
                symbol_depth['bid3_price'] = item['b'][2][0]
                symbol_depth['bid3_size'] = item['b'][2][1]

            if ask_depth_len >=2 :
                symbol_depth['ask2_price'] = item['a'][1][0]
                symbol_depth['ask2_size'] = item['a'][1][1]

            if ask_depth_len >=3 :
                symbol_depth['ask3_price'] = item['a'][2][0]
                symbol_depth['ask3_size'] = item['a'][2][1]

            ret_data[symbol] = symbol_depth

        return ret_data
    # def open_orders(self, clOrdIDPrefix):
    #     '''Get all your open orders.'''
    #     orders = self.data['order']
    #     # Filter to only open orders and those that we actually placed
    #     return [o for o in orders if str(o['clOrdID']).startswith(clOrdIDPrefix) and order_leaves_quantity(o)]

    # def recent_trades(self):
    #     '''Get recent trades.'''
    #     return self.data['trade']

    #
    # End Public Methods
    #

    def connect(self, path, on_message):
        '''Connect to the websocket in a thread.'''
        self.logger.info("Starting thread")
        # wsURL = "wss://stream.binance.com:9443/ws/"+symbol+"@depth"
        # wsURL = "wss://stream.binance.com:9443/stream?streams=ethbtc@depth/eosbtc@depth/xrpbtc@depth"
        wsURL = self.endpoint + path
        self.ws = websocket.WebSocketApp(wsURL,
                                         on_message=on_message,
                                         on_close=self.__on_close,
                                         on_open=self.__on_open,
                                         on_error=self.__on_error,
                                         header=[]
                                         )

        self.wst = threading.Thread(target=lambda: self.ws.run_forever())
        self.wst.daemon = True
        self.wst.start()
        self.logger.info("Started connect thread "+path)
        # Wait for connect before continuing
        # conn_timeout = 5
        # while not self.ws.sock or not self.ws.sock.connected and conn_timeout:
        #     sleep(5)
        #     conn_timeout -= 1
        # if not conn_timeout:
        #     self.logger.error("Couldn't connect to WS! Exiting.")
        #     self.exit()
        #     raise websocket.WebSocketTimeoutException('Couldn\'t connect to WS! Exiting.')
        while not self.ws.sock or not self.ws.sock.connected :
            self.logger.info("wait for connecting... "+path)
            sleep(5)

    # def __get_auth(self):
    #     '''Return auth headers. Will use API Keys if present in settings.'''
    #     if self.api_key:
    #         self.logger.info("Authenticating with API Key.")
    #         # To auth to the WS using an API key, we generate a signature of a nonce and
    #         # the WS API endpoint.
    #         expires = generate_nonce()
    #         return [
    #             "api-expires: " + str(expires),
    #             "api-signature: " + generate_signature(self.api_secret, 'GET', '/realtime', expires, ''),
    #             "api-key:" + self.api_key
    #         ]
    #     else:
    #         self.logger.info("Not authenticating.")
    #         return []

    # def __get_url(self):
    #     '''
    #     Generate a connection URL. We can define subscriptions right in the querystring.
    #     Most subscription topics are scoped by the symbol we're listening to.
    #     '''

    #     # You can sub to orderBookL2 for all levels, or orderBook10 for top 10 levels & save bandwidth
    #     symbolSubs = ["execution", "instrument", "order", "orderBookL2_25", "position", "quote", "trade"]
    #     genericSubs = ["margin"]

    #     subscriptions = [sub + ':' + self.symbol for sub in symbolSubs]
    #     subscriptions += genericSubs

    #     urlParts = list(urllib.parse.urlparse(self.endpoint))
    #     urlParts[0] = urlParts[0].replace('http', 'ws')
    #     urlParts[2] = "/realtime?subscribe={}".format(','.join(subscriptions))
    #     return urllib.parse.urlunparse(urlParts)

    # def __wait_for_account(self):
    #     '''On subscribe, this data will come down. Wait for it.'''
    #     # Wait for the keys to show up from the ws
    #     while not {'margin', 'position', 'order', 'orderBookL2_25'} <= set(self.data):
    #         sleep(0.1)

    # def __wait_for_symbol(self, symbol):
    #     '''On subscribe, this data will come down. Wait for it.'''
    #     while not {'instrument', 'trade', 'quote'} <= set(self.data):
    #         sleep(0.1)

    # def __send_command(self, command, args=None):
    #     '''Send a raw command.'''
    #     if args is None:
    #         args = []
    #     self.ws.send(json.dumps({"op": command, "args": args}))

    def __on_message(self, message):
        '''Handler for parsing WS messages.'''
        message = json.loads(message)
        self.logger.debug(json.dumps(message))

        # table = message['table'] if 'table' in message else None
        # action = message['action'] if 'action' in message else None
        try:
            self.data = message
            # if 'subscribe' in message:
            #     self.logger.debug("Subscribed to %s." % message['subscribe'])
            # elif action:

            #     if table not in self.data:
            #         self.data[table] = []

            #     # There are four possible actions from the WS:
            #     # 'partial' - full table image
            #     # 'insert'  - new row
            #     # 'update'  - update row
            #     # 'delete'  - delete row
            #     if action == 'partial':
            #         self.logger.debug("%s: partial" % table)
            #         self.data[table] += message['data']
            #         # Keys are communicated on partials to let you know how to uniquely identify
            #         # an item. We use it for updates.
            #         self.keys[table] = message['keys']
            #     elif action == 'insert':
            #         self.logger.debug('%s: inserting %s' % (table, message['data']))
            #         self.data[table] += message['data']

            #         # Limit the max length of the table to avoid excessive memory usage.
            #         # Don't trim orders because we'll lose valuable state if we do.
            #         if table not in ['order', 'orderBookL2_25'] and len(self.data[table]) > BitMEXWebsocket.MAX_TABLE_LEN:
            #             self.data[table] = self.data[table][int(BitMEXWebsocket.MAX_TABLE_LEN / 2):]

            #     elif action == 'update':
            #         self.logger.debug('%s: updating %s' % (table, message['data']))
            #         # Locate the item in the collection and update it.
            #         for updateData in message['data']:
            #             item = findItemByKeys(self.keys[table], self.data[table], updateData)
            #             if not item:
            #                 return  # No item found to update. Could happen before push
            #             item.update(updateData)
            #             # Remove cancelled / filled orders
            #             if table == 'order' and not order_leaves_quantity(item):
            #                 self.data[table].remove(item)
            #     elif action == 'delete':
            #         self.logger.debug('%s: deleting %s' % (table, message['data']))
            #         # Locate the item in the collection and remove it.
            #         for deleteData in message['data']:
            #             item = findItemByKeys(self.keys[table], self.data[table], deleteData)
            #             self.data[table].remove(item)
            #     else:
            #         raise Exception("Unknown action: %s" % action)
        except:
            self.logger.error(traceback.format_exc())

    def __on_error(self, error):
        '''Called on fatal websocket errors. We exit on these.'''
        if not self.exited:
            self.logger.error("Error : %s" % error)
            raise websocket.WebSocketException(error)

    def __on_open(self):
        '''Called when the WS opens.'''
        self.logger.info("Websocket Opened.")

    def __on_close(self):
        '''Called on websocket close.'''
        self.logger.info('Websocket Closed')
