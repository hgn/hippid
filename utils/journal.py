import os
import time
import markdown
import shutil
import datetime
import json

from utils import helper

def gc(app):
    max_entries = 500
    if 'journal_max_entries' in app['CONF']:
        max_entries = int(app['CONF']['journal_max_entries'])
    path_logfile = os.path.join(app['PATH-DB'], 'journal.json')
    journal_db = list()
    with open(path_logfile) as fd:
        for line in fd:
            journal_db.append(line)
    if len(journal_db) <= max_entries:
        # nothing
        return
    over = len(journal_db) - max_entries
    journal_shortend = journal_db[over:]
    new_log = ''
    for entry in journal_shortend:
        new_log += "{}".format(entry)
    with open(path_logfile, 'w') as fd:
        fd.write(new_log)


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

