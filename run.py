#!/usr/bin/python3
# coding: utf-8

import os
import sys
import datetime
import random
import argparse
import asyncio
import time
import tempfile
import shutil
import glob

from aiohttp import web

from utils import api_ping
from utils import upload
from utils import generator
from utils import journal
from utils import gc
from utils import page_main
from utils import page_journal
from utils import page_disk_info

try:
    import pympler.summary
    import pympler.muppy
except:
    pympler = None


APP_VERSION = "001"

# exit codes for shell, failures can later be sub-devided
# if required and shell/user has benefit of this information
EXIT_OK      = 0
EXIT_FAILURE = 1



def set_config_defaults(app):
    # CAN be overwritten by config, will
    # be checked for sanity before webserver start
    app['MAX_REQUEST_SIZE'] = 5000000

def init_aiohttp(conf):
    loop = asyncio.get_event_loop()
    app = web.Application(loop=loop)
    app["CONF"] = conf
    app['QUEUE'] = asyncio.Queue(maxsize=64)
    app['LOOP'] = loop
    return app

async def handle_journal(request):
    root = request.app['path-root']
    full = os.path.join(root, "httpd/assets/webpage/journal.html")
    with open(full, 'r') as content_file:
        content = str.encode(content_file.read())
        return web.Response(body=content, content_type='text/html')

async def handle_utilization(request):
    root = request.app['path-root']
    full = os.path.join(root, "httpd/assets/webpage/utilization.html")
    with open(full, 'r') as content_file:
        content = str.encode(content_file.read())
        return web.Response(body=content, content_type='text/html')

async def handle_index(request):
    path = os.path.join(request.app['PATH-GENERATE'], 'index.html')
    if not os.path.isfile(path):
        return web.Response(text="NO DATA YET - SRY")
    with open(path, 'r') as content_file:
        content = str.encode(content_file.read())
        return web.Response(body=content, content_type='text/html')


def setup_routes(app, conf):
    app.router.add_route('*', '/api/v1/ping', api_ping.handle)
    app.router.add_route('*', '/api/v1/upload', upload.handle)
    path_assets = os.path.join(app['PATH-TEMPLATES'], 'assets')
    app.router.add_static('/assets/', path_assets, show_index=True)
    app.router.add_get('/', handle_index)
    app.router.add_route('*', '/journal', page_journal.handle)
    app.router.add_route('*', '/disk-info', page_disk_info.handle)
    app.router.add_route('*', '/❤️/{path:.*}', page_main.handle)


def gc_purge_outdated(app):
    gc_major_lifetime_max = 60 * 60 * 24 * 7 * 52
    if 'gc_major_lifetime_max' in app['CONF']:
        gc_major_lifetime_max = app['CONF']['gc_major_lifetime_max']
    gc.run(app, gc_major_lifetime_max)


def gc_exec(app):
    gc_purge_outdated(app)
    try:
        app['QUEUE'].put_nowait(None)
    except:
        print("the generator was already informed, ignore it, no need to regenerate")


def gc_majors_register(app):
    if 'gc_interval' not in app['CONF']:
        journal.log(app, 'no garbage collection interval specified - gc disabled!')
        return
    interval = app['CONF']['gc_interval']
    call_time = app['LOOP'].time() + interval
    msg = "register next gc timeout in {} seconds".format(interval)
    journal.log(app, msg)
    app['LOOP'].call_at(call_time, gc_majors_register, app)
    gc_exec(app)


def setup_gc_majors(app):
    gc_majors_register(app)

def seconds_to_midnight():
    now = datetime.datetime.now()
    deltatime = datetime.timedelta(days=1)
    tomorrow = datetime.datetime.replace(now + deltatime, hour=0, minute=0, second=0)
    seconds = (tomorrow - now).seconds
    if seconds < 60: return 60.0 # sanity checks
    if seconds > 60 * 60 * 24: return 60.0 * 60 * 24
    return seconds

def gc_journal_register(app):
    interval = app['CONF']['gc_interval']
    wait_time = seconds_to_midnight()
    call_time = app['LOOP'].time() + wait_time
    msg = "register next journal gc timeout in {} minutes".format(wait_time // 60)
    journal.log(app, msg)
    app['LOOP'].call_at(call_time, gc_journal_register, app)
    journal.gc(app)

def setup_gc_journal(app):
    gc_journal_register(app)

def setup_early(app):
    app['DEBUG'] = False
    if 'debug' in app['CONF']:
        if app['CONF']['debug'] == True:
            app['DEBUG'] = True


def setup_paths(app):
    app['path-root'] = os.path.dirname(os.path.realpath(__file__))
    if not 'db_path' in app["CONF"]:
        app['PATH-DB'] = os.path.join(tempfile.mkdtemp())
    else:
        app['PATH-DB'] = os.path.join(app["CONF"]['db_path'])
    print('DB path: {}'.format(app['PATH-DB']))
    os.makedirs(app['PATH-DB'], exist_ok=True)

async def recuring_memory_output(conf):
    while True:
        objects = pympler.muppy.get_objects()
        sum1 = pympler.summary.summarize(objects)
        pympler.summary.print_(sum1)
        await asyncio.sleep(60)


def init_debug_memory(conf):
    if not pympler:
        print("pympler not installed, memory_debug not possible")
        return
    asyncio.ensure_future(recuring_memory_output(conf))


def init_debug(conf):
    if 'memory_debug' in conf and conf['memory_debug']:
        init_debug_memory(conf)


def setup_db_path(app):
    if not 'db_path' in app["CONF"]:
        app['PATH-DB'] = os.path.join(tempfile.mkdtemp())
    else:
        app['PATH-DB'] = os.path.join(app["CONF"]['db_path'])
    print('DB path: {}'.format(app['PATH-DB']))
    os.makedirs(app['PATH-RAW'], exist_ok=True)


def setup_page_dir(app):
    app['PATH-GENERATE'] = os.path.join(app['PATH-DB'], "generated")
    print('DB Generated: {}'.format(app['PATH-GENERATE']))
    if os.path.exists(app['PATH-GENERATE']):
        #print("remove generate_path first: {}".format(app['PATH-GENERATE']))
        shutil.rmtree(app['PATH-GENERATE'])
    os.makedirs(app['PATH-GENERATE'], exist_ok=True)

def setup_raw(app):
    app['PATH-RAW'] = os.path.join(app['PATH-DB'], "raw")
    print('DB RAW: {}'.format(app['PATH-RAW']))
    os.makedirs(app['PATH-RAW'], exist_ok=True)


def setup_template_files(app):
    if not 'template_dir' in app["CONF"]:
        app['PATH-TEMPLATES'] = os.path.join(app['path-root'], "templates")
    else:
        app['PATH-TEMPLATES'] = app["CONF"]['template_dir']
    if not os.path.exists(app['PATH-TEMPLATES']):
        raise('templates_dir does not exists, check your config')
    # read header and footer
    full = os.path.join(app['PATH-TEMPLATES'], 'header.html')
    with open(full, 'r') as fd:
        app['BLOB-HEADER'] = fd.read()
    full = os.path.join(app['PATH-TEMPLATES'], 'footer.html')
    with open(full, 'r') as fd:
        app['BLOB-FOOTER'] = fd.read()
    # now copy assets recursively
    src = os.path.join(app['PATH-TEMPLATES'], 'assets')
    dst = app['PATH-GENERATE'] + '/assets'
    shutil.copytree(src, dst)

    #for filename in glob.glob(os.path.join(directory, '*.*')):
    #    shutil.copy(filename, app["CONF"]['page_dir'])

def setup_generator(app):
    app['LOOP'].create_task(generator.generator(app))

def main(conf):
    init_debug(conf)
    app = init_aiohttp(conf)
    setup_early(app)
    setup_paths(app)
    journal.log(app, 'start sequence hippid')
    setup_page_dir(app)
    setup_raw(app)
    setup_template_files(app)
    setup_routes(app, conf)
    setup_gc_majors(app)
    setup_gc_journal(app)
    setup_generator(app)
    web.run_app(app, host="::", port=8080)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--configuration", help="configuration", type=str, default=None)
    parser.add_argument("-v", "--verbose", help="verbose", action='store_true', default=False)
    args = parser.parse_args()
    if not args.configuration:
        emsg = "Configuration required, please specify a valid file path, exiting now"
        sys.stderr.write("{}\n".format(emsg))
        emsg = "E.g.: \"./run.py -f assets/monetta.conf\""
        sys.stderr.write("{}\n".format(emsg))
        sys.exit(EXIT_FAILURE)
    return args


def load_configuration_file(args):
    config = dict()
    exec(open(args.configuration).read(), config)
    return config

def configuration_check(conf):
    if not "host" in conf.common:
        conf.common.host = '0.0.0.0'
    if not "port" in conf.common:
        conf.common.port = '8080'

    if not "path" in conf.db:
        sys.stderr.write("No path configured for database, but required! Please specify "
                         "a path in db section\n")
        sys.exit(EXIT_FAILURE)

def conf_init():
    args = parse_args()
    conf = load_configuration_file(args)
    return conf

if __name__ == '__main__':
    info_str = sys.version.replace('\n', ' ')
    conf = conf_init()
    main(conf)
