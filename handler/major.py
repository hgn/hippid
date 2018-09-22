import os
import time

from aiohttp import web

def handle(request):
    major_id = request.match_info['major_id']
    path = os.path.join(request.app['PATH-GENERATE'], major_id, 'index.html')
    if not os.path.isfile(path):
        return web.Response(text="NOPE")
    with open(path, 'r') as content_file:
        content = str.encode(content_file.read())
        return web.Response(body=content, content_type='text/html')
