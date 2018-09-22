import os
import time

from aiohttp import web

def handle(request):
    return web.Response(text="NOPE")
