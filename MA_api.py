
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine,and_
from sqlalchemy.orm import sessionmaker
import traceback,time
from sanic import Sanic
from sanic import response
import aiohttp
import json
from MA_calc import fetch_latest_diff_data,tv_data_fetch
from db.model import Base, SessionContextManager,BKQuoteOrder

fake_data={"t":[1507852800,1508112000,1508198400,1508284800,1508371200,1508457600,1508716800,1508803200,1508889600,1508976000,1509062400,1509321600,1509408000,1509494400,1509580800,1509667200,1509926400,1510012800,1510185600,1510272000,1510531200,1510617600,1510704000,1510790400,1510876800,1511136000,1511222400,1511308800,1511481600,1511740800,1511827200,1511913600,1512000000,1512086400,1512345600,1512432000,1512518400,1512604800,1512691200,1512950400,1513036800,1513123200,1513209600,1513296000,1513555200,1513641600,1513728000,1513814400,1513900800,1514246400,1514332800,1514419200,1514505600,1514851200,1514937600,1515024000,1515110400,1515369600,1515456000,1515542400,1515628800,1515715200,1516060800,1516147200,1516233600,1516320000,1516579200,1516665600,1516752000,1516838400,1516924800,1517184000,1517270400,1517356800,1517443200,1517529600,1517788800,1517875200,1517961600,1518048000,1518134400,1518393600,1518480000,1518566400,1518652800,1518739200,1519084800,1519171200,1519257600,1519344000,1519603200,1519689600,1519776000,1519862400,1519948800,1520208000,1520294400,1520380800,1520467200,1520553600,1520812800,1520899200,1520985600,1521072000,1521158400,1521417600,1521504000,1521590400,1521676800,1521763200,1522022400],"o":[156.73,157.9,159.78,160.42,156.75,156.61,156.89,156.29,156.91,157.23,159.29,163.89,167.9,169.87,167.64,174,172.365,173.91,175.11,175.11,173.5,173.04,169.97,171.18,171.04,170.29,170.78,173.36,175.1,175.05,174.3,172.63,170.43,169.95,172.48,169.06,167.5,169.03,170.49,169.2,172.15,172.5,172.4,173.63,174.88,175.03,174.87,174.17,174.68,170.8,170.1,171,170.52,170.16,172.53,172.54,173.44,174.35,174.55,173.16,174.59,176.18,177.9,176.15,179.37,178.61,177.3,177.3,177.25,174.505,172,170.16,165.525,166.87,167.165,166,159.1,154.83,163.085,160.29,157.07,158.5,161.95,163.045,169.79,172.36,172.05,172.83,171.8,173.67,176.35,179.1,179.26,178.54,172.8,175.21,177.91,174.94,175.48,177.96,180.29,182.59,180.32,178.5,178.65,177.32,175.24,175.04,170,168.39,168.07],"h":[156.73,157.9,159.78,160.42,156.75,156.61,156.89,156.29,156.91,157.23,159.29,163.89,167.9,169.87,167.64,174,172.365,173.91,175.11,175.11,173.5,173.04,169.97,171.18,171.04,170.29,170.78,173.36,175.1,175.05,174.3,172.63,170.43,169.95,172.48,169.06,167.5,169.03,170.49,169.2,172.15,172.5,172.4,173.63,174.88,175.03,174.87,174.17,174.68,170.8,170.1,171,170.52,170.16,172.53,172.54,173.44,174.35,174.55,173.16,174.59,176.18,177.9,176.15,179.37,178.61,177.3,177.3,177.25,174.505,172,170.16,165.525,166.87,167.165,166,159.1,154.83,163.085,160.29,157.07,158.5,161.95,163.045,169.79,172.36,172.05,172.83,171.8,173.67,176.35,179.1,179.26,178.54,172.8,175.21,177.91,174.94,175.48,177.96,180.29,182.59,180.32,178.5,178.65,177.32,175.24,175.04,170,168.39,168.07],"l":[156.73,157.9,159.78,160.42,156.75,156.61,156.89,156.29,156.91,157.23,159.29,163.89,167.9,169.87,167.64,174,172.365,173.91,175.11,175.11,173.5,173.04,169.97,171.18,171.04,170.29,170.78,173.36,175.1,175.05,174.3,172.63,170.43,169.95,172.48,169.06,167.5,169.03,170.49,169.2,172.15,172.5,172.4,173.63,174.88,175.03,174.87,174.17,174.68,170.8,170.1,171,170.52,170.16,172.53,172.54,173.44,174.35,174.55,173.16,174.59,176.18,177.9,176.15,179.37,178.61,177.3,177.3,177.25,174.505,172,170.16,165.525,166.87,167.165,166,159.1,154.83,163.085,160.29,157.07,158.5,161.95,163.045,169.79,172.36,172.05,172.83,171.8,173.67,176.35,179.1,179.26,178.54,172.8,175.21,177.91,174.94,175.48,177.96,180.29,182.59,180.32,178.5,178.65,177.32,175.24,175.04,170,168.39,168.07],"c":[156.73,157.9,159.78,160.42,156.75,156.61,156.89,156.29,156.91,157.23,159.29,163.89,167.9,169.87,167.64,174,172.365,173.91,175.11,175.11,173.5,173.04,169.97,171.18,171.04,170.29,170.78,173.36,175.1,175.05,174.3,172.63,170.43,169.95,172.48,169.06,167.5,169.03,170.49,169.2,172.15,172.5,172.4,173.63,174.88,175.03,174.87,174.17,174.68,170.8,170.1,171,170.52,170.16,172.53,172.54,173.44,174.35,174.55,173.16,174.59,176.18,177.9,176.15,179.37,178.61,177.3,177.3,177.25,174.505,172,170.16,165.525,166.87,167.165,166,159.1,154.83,163.085,160.29,157.07,158.5,161.95,163.045,169.79,172.36,172.05,172.83,171.8,173.67,176.35,179.1,179.26,178.54,172.8,175.21,177.91,174.94,175.48,177.96,180.29,182.59,180.32,178.5,178.65,177.32,175.24,175.04,170,168.39,168.07],"v":[16287608,23894630,18816438,16158659,42111326,23612246,21654461,17137731,20126554,16751691,43904150,43923292,35474672,33100847,32710040,58683826,34242566,23910914,28636531,25061183,16828025,23588451,28702351,23497326,21665811,15974387,24875471,24997274,14026519,20536313,25468442,40788324,40172368,39590080,32115052,27008428,28224357,24469613,23096872,33092051,18945457,23142242,20219307,37054632,28831533,27078872,23000392,20356826,16052615,32968167,21672062,15997739,25643711,25048048,28819653,22211345,23016177,20134092,21262614,23589129,17523256,25039531,29159005,32752734,30234512,30827809,26023683,31702531,50562257,39661804,37121805,48434424,45137026,30984099,38099665,85436075,66090446,66625484,50852130,49594129,66723743,60560145,32104756,39669178,50609595,39638793,33531012,35833514,30504116,33329232,36886432,38685165,33604574,48801970,38453950,28401366,23788506,31703462,23163767,31385134,32055405,31168404,29075469,22584565,36836456,32804695,19314039,35247358,41051076,40248954,36272617],"s":"ok"}

fake_style_data = {
    "name":"bianace/bitmex",
    "exchange-traded":"OrangeGrin",
    "exchange-listed":"OrangeGrin",
    "timezone":"America/New_York",
    "minmov":1,
    "minmov2":0,
    "pointvalue":1,
    "session":"0930-1630",
    "has_intraday":False,
    "has_no_volume":True,
    "description":"BitCoin",
    "type":"bitcoin",
    "supported_resolutions":["S","M","H","D","2D","3D","W","3W","M","6M"],
    "pricescale":100,
    "ticker":"AAPL"
    }

fake_config_data = {
    "supports_search":True,
    "supports_group_request":True,
    "supports_marks":True,
    "supports_timescale_marks":True,
    "supports_time":True,
    "exchanges":[
        {"value":"OrangeGrin","name":"OrangeGrin","desc":"OrangeGrin"}
        ],
        "symbols_types":[
            {"name":"All types","value":""},
            {"name":"Stock","value":"stock"},
            {"name":"Index","value":"index"}
            ],
        "supported_resolutions":["S","M","H","D","2D","3D","W","3W","M","6M"]
}

dburl = URL(**{
    "drivername": "postgresql+psycopg2",
    # "host": "150.109.52.225",
    # "host": "198.13.38.21",
    "host": "127.0.0.1",
    "port": 5432,
    "username": "ray",
    "password": "yqll",
    "database": "dashpoint"
    })
engine = create_engine(dburl, echo=False)
Session = sessionmaker(bind=engine, class_=SessionContextManager)
Base.metadata.create_all(bind=engine)

app = Sanic(__name__)

async def fetch(session, url):
    """
    Use session object to perform 'get' request on url
    """
    async with session.get(url) as result:
        return await result.json()


@app.route('/')
async def handle_request(request):
    url = "https://api.github.com/repos/channelcat/sanic"
    
    async with aiohttp.ClientSession() as session:
        result = await fetch(session, url)
        return response.json(result)

@app.get('/history')
def get_history_route(request):
    print(request.raw_args)
    # for k in ['o','h','l','c']:
    #     fake_data[k] = [v/100 for v in fake_data[k]]
    # return response.json(fake_data,headers={'Access-Control-Allow-Origin': '*','Access-Control-Allow-Methods': '*'})

    with Session() as session:
        data_body = tv_data_fetch(session,'bitmex','asks','binance','bids','ETH',request.raw_args['resolution'],request.raw_args['from'],request.raw_args['to'])
        if data_body:
            data_body['h'] = data_body['o']
            data_body['l'] = data_body['o']
            data_body['v'] = [0]*len(data_body['o']) 
            data_body['c'] = data_body['o']
            data_body['s'] = 'ok'
        else:

            data_body = {"s":"no_data","nextTime":int(time.time())+60}
        return response.json(data_body,headers={'Access-Control-Allow-Origin': '*','Access-Control-Allow-Methods': '*'})

@app.get('/time')
def get_sever_time_route(request):
    print(request.raw_args)
    return response.json(int(time.time()),headers={'Access-Control-Allow-Origin': '*','Access-Control-Allow-Methods': '*'})

@app.get('/symbols')
def get_symbols_route(request):
    print(request.raw_args)
    return response.json(fake_style_data,headers={'Access-Control-Allow-Origin': '*','Access-Control-Allow-Methods': '*'})

@app.get('/symbol_info')
def get_symbol_info_route(request):
    print(request.raw_args)
    return response.json({
   "symbol": ["AAPL", "ETH_BABT", "SPX"],
   "description": ["Apple Inc", "ETH_Bianace_Bitmex", "S&P 500 index"],
   "exchange-listed": "ORANGE GRIN",
   "exchange-traded": "ORANGE GRIN",
   "minmov": 1,
   "minmov2": 0,
   "pricescale": [1, 1, 100],
   "has-dwm": True,
   "has-intraday": True,
   "has-no-volume": [False, False, True],
   "type": ["stock", "bitcoin", "index"],
   "ticker": ["AAPL~0", "ETH_BABT", "$SPX500"],
   "timezone": "Etc/UTC",
   "session-regular": "0900-1600",
},headers={'Access-Control-Allow-Origin': '*','Access-Control-Allow-Methods': '*'})

# @app.get('/config')
# def get_config_route(request):
#     print(request.raw_args)
#     return response.json({},headers={'Access-Control-Allow-Origin': '*'})

@app.get('/diff')
def get_maavg_value_route(request):

    print(request.raw_args)
    ret_data = {"status":0,"msg":"param error!"}
    if request.raw_args.get("exchangeA",None) and  request.raw_args.get("exchangeB",None) and request.raw_args.get("symbol",None):
        with Session() as session:
            ret = fetch_latest_diff_data(session,request.raw_args["exchangeA"],request.raw_args["exchangeB"],request.raw_args["symbol"])
            if ret:
                ret_data["data"]=ret
                ret_data["status"] = 1
                ret_data["msg"] = "success!"
            else:
                ret_data["status"] = 2
                ret_data["msg"] = "query fail,check param!"
    return response.json(ret_data)

@app.get('/fundingRate')
def get_funding_rate(request):
    print(request.raw_args)
    ret_data = {"status":0,"msg":"param error!"}
    try:
        if request.raw_args.get("symbol",None):
            with open('./fundingRate.log','r') as fp:
                funding_rate_dict = json.load(fp)
                print(funding_rate_dict)
                ret = funding_rate_dict.get(request.raw_args["symbol"].upper(),None)
                if ret:
                    ret_data["data"]={'value':ret['fundingRate'],"timestamp":ret['timestamp'],"symbol":request.raw_args["symbol"].upper()}
                    ret_data["status"] = 1
                    ret_data["msg"] = "success!"
                else:
                    ret_data["status"] = 2
                    ret_data["msg"] = "query fail,check param!"
    except Exception:
        print(traceback.format_exc())
    
    return response.json(ret_data)
    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, workers=1)