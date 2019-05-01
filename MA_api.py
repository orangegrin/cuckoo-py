
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine,and_
from sqlalchemy.orm import sessionmaker
import traceback,time
from sanic import Sanic
from sanic import response
import aiohttp

from db.model import Base, SessionContextManager,BKQuoteOrder


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


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, workers=2)