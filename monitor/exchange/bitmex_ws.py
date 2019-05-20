import json
import requests
import urllib
import time
import hashlib
import hmac
import configparser
import logging
import asyncio
import websockets

class BitmexWs(object):
    def __init__(self, api_key, api_secret):
        self.api_key =  api_key
        self.api_secret = api_secret
        self.url = 'https://api.binance.com'



    async def hello():
        async with websockets.connect(
                'ws://localhost:8765') as ws:
            name = input("What's your name? ")
            await ws.send(name)
            greeting = await ws.recv()

