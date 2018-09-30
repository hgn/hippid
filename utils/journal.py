import os
import time
import markdown
import shutil
import datetime
import json

from utils import helper

def _log_write(app, entry):
    path_logfile = os.path.join(app['PATH-DB'], 'journal.json')
    dj = json.dumps(entry, sort_keys=True, separators=(',', ': '))
    with open(path_logfile, 'a') as fd:
        fd.write(dj + '\n')

def log(app, msg, severity='info', asynchronous=False):
    entry = dict()
    entry['timestamp'] = helper.timestr()
    entry['severity'] = severity
    entry['msg'] = msg
    if not asynchronous:
        _log_write(app, entry)
    else:
        app['LOOP'].call_later(0.005, functools.partial(_log_write, app, entry))

