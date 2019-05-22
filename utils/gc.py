import os
import time
import markdown
import shutil
import datetime
import json

from utils import journal
from utils import helper
from utils import upload

def is_extended(path_major_id):
    ret = False
    path = os.path.join(path_major_id, upload.PATH_ATTRIBUTES, 'lifetime.json')
    if os.path.exists(path):
        ret = True
    return ret

def gc_outdated_list(app, lifetime_standard, lifetime_extended):
    ''' return a sorted object based list of id's with meta-data'''
    now = datetime.datetime.utcnow()
    ret = list()
    for major_id in os.listdir(app['PATH-RAW']):
        full = os.path.join(app['PATH-RAW'], major_id)
        if not os.path.isdir(full):
            continue
        path_meta_self_file = os.path.join(full, upload.PATH_META_SELF,  'access.json')
        with open(path_meta_self_file) as f:
            meta_data = json.load(f)
        modified_last = helper.hippid_date_parse(meta_data['time-last'])
        age = (now - modified_last).total_seconds()
        extended_lifetime = is_extended(full)
        if extended_lifetime:
            lifetime = lifetime_extended
        else:
            lifetime = lifetime_standard
        if age > lifetime:
            ret.append([major_id, full, (age - lifetime)])
    return ret

def run(app, lifetime_standard, lifetime_extended):
    outdated = gc_outdated_list(app, lifetime_standard, lifetime_extended)
    for outdate in outdated:
        msg = "gc detected outdated entry: {} (outdated since {} seconds) - removed".format(outdate[0], outdate[2])
        journal.log(app, msg)
        shutil.rmtree(outdate[1])

