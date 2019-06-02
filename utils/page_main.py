import os
import time
import re
import mimetypes

from aiohttp import web

RE_WITH_DOT = re.compile(r'(.*\.\S+)')
RE_FINAL_SLASH = re.compile('(.*)\/$')
RE_NO_SLASH = re.compile(r'([^\/]*)')

def content_index(request, path):
    path = os.path.join(request.app['PATH-GENERATE-ID'], path, 'index.html')
    if not os.path.isfile(path):
        return web.Response(text="File not available: {}, SRY, ¯\_(ツ)_/¯".format(path))
    with open(path, 'r') as content_file_fd:
        content = str.encode(content_file_fd.read())
        return web.Response(body=content, content_type='text/html')


def content_file(request, path):
    path = os.path.join(request.app['PATH-GENERATE-ID'], path)
    if not os.path.isfile(path):
        print(path + " not available")
        return web.Response(text="File not available: {}, SRY, ¯\_(ツ)_/¯".format(path))
    with open(path, 'br') as content_file_fd:
        content = content_file_fd.read()
    mime_type, _ = mimetypes.guess_type(path)
    if os.path.basename(path).startswith('attribute.'):
        # default to octet-stream for unknown data BUT if it is an
        # attribute, it MUST be JSON
        mime_type = 'application/json'
    if mime_type is None:
        mime_type = "binary/octet-stream"
    return web.Response(body=content, content_type=mime_type)


def handle(request):
    path = request.match_info['path']
    m = RE_FINAL_SLASH.match(path)
    if m:
        #return web.Response(text="RE_FINAL_SLASH {}".format(m.group(0)))
        return content_index(request, m.group(0))

    m = RE_NO_SLASH.match(path)
    if m and path.find('/') == -1:
        #return web.Response(text="RE_NO_SLASH {}".format(m.group(0)))
        return content_index(request, m.group(0))

    m = RE_WITH_DOT.match(path)
    if m:
        #return web.Response(text="RE_WITH_DOT {}".format(m.group(0)))
        return content_file(request, m.group(0))

    return web.Response(text="internal error - FIXME")
