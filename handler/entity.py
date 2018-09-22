#!/usr/bin/python3
# coding: utf-8

import json
import os
import datetime
import time
import sys

import aiohttp

def timestr():
    dt = datetime.datetime.utcnow()
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')


def process_minor(request, obj):
    return aiohttp.web.Response(text="All right!")


def save_meta_data_existing(obj, major_path):
    pass


def save_meta_data_new(obj, major_path):
    """ meta-own.json and meta-foreign.json """
    path = os.path.join(major_path, '.meta-own.json')
    d = dict()
    now = timestr()
    d['time-first'] = now
    d['time-last'] = now
    d['submitters'] = list()
    submitter = dict()
    submitter['name'] = obj['submitter']
    d['submitters'].append(submitter)
    dj = json.dumps(d, sort_keys=True, separators=(',', ': '))
    with open(path, 'w') as fd:
        fd.write(dj)

    path = os.path.join(major_path, '.meta-foreign.json')
    d = dict()
    # FIXME: check key existins
    d['lifetime-group'] = obj['meta']['lifetime-group']
    dj = json.dumps(d, sort_keys=True, separators=(',', ': '))
    with open(path, 'w') as fd:
        fd.write(dj)


def process_major_new(request, obj, major_path):
    os.makedirs(major_path, exist_ok=True)
    save_meta_data_new(obj, major_path)
    for major in obj['majors']:
        path = os.path.join(major_path, major['name'])
        content = major['content']
        with open(path, 'w') as fd:
            fd.write(content)
    request.app['QUEUE'].put_nowait(["MAJOR", obj['major-id']])
    return aiohttp.web.Response(text="All right!")


def process_major_existing(request, obj, major_path):
    return aiohttp.web.Response(text="All right!")


def process_major(request, obj):
    if not 'major-id' in obj:
        return aiohttp.web.Response(status=400, body="message corrupt")
    major_path = os.path.join(request.app['PATH-DB'], obj['major-id'])
    if os.path.exists(major_path):
        return process_major_existing(request, obj, major_path)
    return process_major_new(request, obj, major_path)


async def handle(request):
    obj = await request.json()
    if 'type' in obj and obj['type'] == 'major':
        return process_major(request, obj)
    if 'type' in obj and obj['type'] == 'minor':
        return process_minor(request, obj)
    return aiohttp.web.Response(status=400, body="message corrupt")


