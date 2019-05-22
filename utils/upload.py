#!/usr/bin/python3
# coding: utf-8

import json
import os
import datetime
import time
import sys
import base64

from utils import journal

import aiohttp


PATH_META_SELF = '.meta'
PATH_ATTRIBUTES = '.attributes'


def timestr():
    dt = datetime.datetime.utcnow()
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')


def process_minor(request, obj):
    return aiohttp.web.Response(text="All right!")


def save_meta_data_existing(obj, major_path):
    pass


def save_meta_data_create_dir(major_path):
    path_self_dir = os.path.join(major_path, PATH_META_SELF)
    os.makedirs(path_self_dir, exist_ok=False)
    path_forgein_dir = os.path.join(major_path, PATH_ATTRIBUTES)
    os.makedirs(path_forgein_dir, exist_ok=False)
    return path_self_dir


def meta_data_init(obj, major_path):
    os.makedirs(major_path, exist_ok=True)
    path_meta_data = save_meta_data_create_dir(major_path)
    path_self_file = os.path.join(path_meta_data, 'access.json')
    d = dict()
    now = timestr()
    d['time-first'] = now
    d['time-last'] = now
    d['submitters'] = list()
    submitter = dict()
    submitter['name'] = obj['submitter']
    submitter['date'] = now
    d['submitters'].append(submitter)
    dj = json.dumps(d, sort_keys=True, separators=(',', ': '))
    with open(path_self_file, 'w') as fd:
        fd.write(dj)


def meta_data_update(obj, major_path):
    """ meta-own.json and meta-foreign.json """
    path = os.path.join(major_path, PATH_META_SELF, 'access.json')
    with open(path) as f:
        d = json.load(f)
    now = timestr()
    d['time-last'] = now
    submitter = dict()
    submitter['name'] = obj['submitter']
    submitter['date'] = now
    d['submitters'].append(submitter)
    dj = json.dumps(d, sort_keys=True, separators=(',', ': '))
    with open(path, 'w') as fd:
        fd.write(dj)

def update_attributes(obj, major_path):
    for object_ in obj['majors']:
        if not 'type' in object_:
            continue
        if object_['type'] != 'attribute':
            continue

        # ok, only attributes from here on
        if object_['name'] == 'alias':
            path = os.path.join(major_path, PATH_ATTRIBUTES, 'alias.json')
            d = dict()
            d['name'] =  object_['content']
            dj = json.dumps(d, sort_keys=True, separators=(',', ': '))
            with open(path, 'w') as fd:
                fd.write(dj)
        elif object_['name'] == 'lifetime':
            path = os.path.join(major_path, PATH_ATTRIBUTES, 'lifetime.json')
            d = dict()
            d['name'] =  object_['content']
            dj = json.dumps(d, sort_keys=True, separators=(',', ': '))
            with open(path, 'w') as fd:
                fd.write(dj)


def update_blobs(request, obj, major_path, existing):
    for major in obj['majors']:
        if 'type' in major and major['type'] == 'attribute':
            # not handled here, ignore early
            continue
        path = os.path.join(major_path, major['name'])
        content = major['content']
        mode = 'w'
        if 'base64-encoded' in major:
            content = base64.b64decode(content)
            mode = 'wb'
        # ok, path can be subdir or subsubsub, so create if not created
        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)
        with open(path, mode) as fd:
            fd.write(content)

def process_major_entry(request, obj, major_path, existing=True):
    if existing == False:
        meta_data_init(obj, major_path)
    else:
        meta_data_update(obj, major_path)
    update_attributes(obj, major_path)
    update_blobs(request, obj, major_path, existing)
    request.app['QUEUE'].put_nowait(["MAJOR", obj['major-id']])
    return aiohttp.web.Response(text="All right!")


def process_major(request, obj):
    if not 'major-id' in obj:
        return aiohttp.web.Response(status=400, body="message corrupt")
    major_path = os.path.join(request.app['PATH-RAW'], obj['major-id'])
    if os.path.exists(major_path):
        return process_major_entry(request, obj, major_path, existing=True)
    return process_major_entry(request, obj, major_path, existing=False)

async def handle(request):
    start = time.time()
    obj = await request.json()
    ret = aiohttp.web.Response(status=400, body="message corrupt")
    if 'type' in obj and obj['type'] == 'major':
        ret = process_major(request, obj)
    if 'type' in obj and obj['type'] == 'minor':
        ret = process_minor(request, obj)
    if request.app['DEBUG']:
        peername = request.transport.get_extra_info('peername')
        peer = "unknown"
        if peername is not None:
            peer = '{}:{}'.format(peername[0], peername[1])
        diff = time.time() - start
        msg = 'processed upload request from {} in {:.4f} seconds'.format(peer, diff)
        journal.log(request.app, msg)
    return ret


