import os
import time
import re
import json

from aiohttp import web

from utils import helper

TBL_HEAD = '''
<table class="table table-striped table-hover table-sm">
  <thead>
    <tr>
      <th scope="col">Time</th>
      <th scope="col">Message</th>
      <th scope="col">Severity</th>
    </tr>
  </thead>
  <tbody>
'''

TBL_FOOTER = '''
  </tbody>
</table>
'''

def humanize_date(string):
    d = helper.hippid_date_parse(string)
    return d.strftime('%H:%M:%S - %Y-%m-%d')

def generate_journal_info(request):
    path_logfile = os.path.join(request.app['PATH-DB'], 'journal.json')
    full_journal = ''
    with open(path_logfile) as fd:
        for line in fd:
            entry = json.loads(line)
            tbl  = '<tr>'
            tbl += '<td>' + humanize_date(entry['timestamp']) + '</td>'
            tbl += '<td>' + entry['msg'] + '</td>'
            tbl += '<td>' + entry['severity'] + '</td>'
            tbl += '</tr>\n'
            full_journal = tbl + full_journal
    return full_journal

def generate_journal_page(request):
    page = request.app['BLOB-HEADER']
    page += TBL_HEAD
    page += generate_journal_info(request)
    page += TBL_FOOTER
    page += request.app['BLOB-FOOTER']
    return web.Response(body=page, content_type='text/html')


def handle(request):
    return generate_journal_page(request)
