import os
import time
import re
import json
from os.path import join, getsize

from aiohttp import web

from utils import helper

TBL_HEAD = '''
<table class="table table-striped table-hover table-sm">
  <thead>
    <tr>
      <th scope="col">Directory</th>
      <th scope="col">Size</th>
    </tr>
  </thead>
  <tbody>
'''

TBL_FOOTER = '''
  </tbody>
</table>
'''

def stats_count_info(request):
    root_path = request.app['PATH-DB']
    cpt = 0
    d = dict()
    dirs_data = dict()
    for root, dirs, files in os.walk(root_path, topdown=False):
        cpt += len(files)
        size = sum(getsize(join(root, name)) for name in files)
        subdir_size = sum(dirs_data[join(root,d)] for d in dirs)
        size = dirs_data[root] = size + subdir_size
        if root.find('.meta') != -1:
            # we ignore (internal) meta directories
            continue
        d[root] = size

    ret  = ''
    ret += "<h2>Files Count</h2>Number of files: {}<br /><br />".format(cpt)
    ret += "<h2>Disk Consumption</h2>"
    ret += "Database disk consumption overall: {} MB<br /><br />".format(d[root_path] // (1024*1024))
    ret += "<h4>Resouce Usage Listed by Objects</h4><br />"
    ret += TBL_HEAD
    for k in sorted(d, key=d.get, reverse=True):
        ret += '<tr>'
        ret += "<td>{}</td><td>{}</td>".format(k, d[k])
    ret += TBL_FOOTER
    return ret

def generate_disk_info_page(request):
    page = request.app['BLOB-HEADER']
    page += stats_count_info(request)
    page += request.app['BLOB-FOOTER']
    return web.Response(body=page, content_type='text/html')


def handle(request):
    return generate_disk_info_page(request)
