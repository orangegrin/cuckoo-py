
import redis
import traceback


DIFF_OFFSET_KEY_DICT = {"BTCUZ":"BTCUZ:DIFF:OFFSET"}
PROFIT_RANGE_KEY_DICT = {"BTCUZ":"BTCUZ:PROFIT:RANGE"}
def get_float_value_from_redis(redis_db_conn,redis_key) -> float:
    try:
        val =  float(redis_db_conn.get(redis_key))
        if val is None:
            return 0
        return val
    except:
        print(traceback.format_exc())
        return 0

def set_float_value_to_redis(redis_db_conn,redis_key,value):
    try:
        float(value)
        return redis_db_conn.set(redis_key,value)
    except Exception:
        print(traceback.format_exc())
        return None