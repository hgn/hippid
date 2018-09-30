import os
import time
import markdown
import shutil
import datetime
import json

from utils import journal
from utils.upload import PATH_META_SELF

#= '.meta/self'
PATH_META_FOREIGN = '.meta/foreign'

extensions = ['markdown.extensions.tables', 'fenced_code', 'nl2br']

def hippid_date_parse(string):
    return datetime.datetime.strptime(string, '%Y-%m-%dT%H:%M:%S.%f')

def human_date_delta(date):
    diff = datetime.datetime.utcnow() - date
    s = diff.seconds
    if diff.days == 1:
        return '1 day ago'
    elif diff.days > 1:
        return '{} days ago'.format(diff.days)
    elif s <= 1:
        return 'just now'
    elif s < 60:
        return '{} seconds ago'.format(s)
    elif s < 120:
        return '1 minute ago'
    elif s < 3600:
        return '{} minutes ago'.format(int(s / 60))
    elif s < 7200:
        return '1 hour ago'
    else:
        return '{} hours ago'.format(int(s / 3600))

def create_id_insert(object_list, new):
    if len(object_list) <= 0:
        object_list.append(new)
        return
    for num, object_ in enumerate(object_list):
        if object_.modified_last <= new.modified_last:
            object_list.insert(num, new)
            return
    object_list.append(new)

def analyze_meta_test(major_id, full_path):
    root = full_path
    d = {'passed' : 0, 'failed': 0, 'error' : 0 }
    for path, subdirs, files in os.walk(root):
        for name in files:
            if name != "main.meta":
                continue
            filepath = os.path.join(path, name)
            with open(filepath) as fd:
                meta_test_data = json.load(fd)
            meta_test_data['type'] == 'test'
            if meta_test_data['status'] == 'passed':
                d['passed'] += 1
            if meta_test_data['status'] == 'error':
                d['error'] += 1
            if meta_test_data['status'] == 'failed':
                d['failed'] += 1
    return d

def meta_test_htmlize(d):
    return "Passed:{},Failed:{},Errors:{}".format(d['passed'], d['failed'], d['error'])

def create_id_list(app):
    ''' return a sorted object based list of id's with meta-data'''
    ret_list = list()
    for major_id in os.listdir(app['PATH-RAW']):
        full = os.path.join(app['PATH-RAW'], major_id)
        if not os.path.isdir(full):
            continue
        ret = lambda: None # functions are objets too
        path_meta_self_file = os.path.join(full, PATH_META_SELF,  'meta.json')
        with open(path_meta_self_file) as f:
            meta_data = json.load(f)
        ret.modified_last = hippid_date_parse(meta_data['time-last'])
        ret.modified_first = hippid_date_parse(meta_data['time-last'])
        ret.submitter_last = meta_data['submitters'][-1]['name']
        ret.id = major_id
        ret.meta_test = analyze_meta_test(major_id, full)
        create_id_insert(ret_list, ret)
    return ret_list


def generate_index_table(app):
    tbl = TBL_HEAD
    create_id_list(app)
    for entity in create_id_list(app):
        tbl += '<tr>'
        tbl += '<td><a href="❤️/' + entity.id + '/">' + entity.id + '</a></td>'
        tbl += '<td>' + entity.modified_last.strftime('%Y-%m-%d %H:%M') + ' ('
        tbl +=          human_date_delta(entity.modified_last) + ')</td>'
        tbl += '<td>' + entity.modified_first.strftime('%Y-%m-%d %H:%M') + '</td>'
        tbl += '<td>' + meta_test_htmlize(entity.meta_test) +'</td>'
        tbl += '<td>' + entity.submitter_last +'</td>'
        tbl += '</tr>'
    tbl += TBL_FOOTER
    return tbl

def generate_index_header(app):
    return '<h2>Overview</h2>'

def generate_index(app):
    new_index = app['BLOB-HEADER']
    new_index += generate_index_header(app)
    new_index += generate_index_table(app)
    new_index += app['BLOB-FOOTER']
    path = os.path.join(app['PATH-GENERATE'], 'index.html')
    with open(path, 'w') as fd:
        fd.write(new_index)

def process_md(app, full):
    cnd = ''
    with open(full, 'r') as fd:
        cnt = fd.read()
    html = markdown.markdown(cnt, extensions=extensions)
    return html

from shutil import *
def copytree(src, dst, symlinks=False, ignore=None):
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not os.path.isdir(dst): # This one line does the trick
        os.makedirs(dst)
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore)
            else:
                # Will raise a SpecialFileError for unsupported file types
                copy2(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            errors.extend(err.args[0])
        except EnvironmentError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        copystat(src, dst)
    except OSError as why:
        if WindowsError is not None and isinstance(why, WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.extend((src, dst, str(why)))
    if errors:
        raise Error(errors)

def process_remain(app, full, dst):
    """ simple copy the rest """
    for dir_part in full.split('/'):
        if dir_part.startswith('.'):
            # v1.2.4/.meta/foreign is ignored
            return
    shutil.copyfile(full, dst)

def generate_major_page(app, major_id, src_path, dst_path):
    os.makedirs(dst_path, exist_ok=True)
    index = app['BLOB-HEADER']
    for filename in sorted(os.listdir(src_path)):
        full = os.path.join(src_path, filename)
        if os.path.isdir(full):
            # do it recursevily
            src_path_tmp = os.path.join(src_path, filename)
            dst_path_tmp = os.path.join(dst_path, filename)
            generate_major_page(app, major_id, src_path_tmp, dst_path_tmp)
        elif filename.endswith('.md'):
            index += process_md(app, full)
        elif filename.startswith('.'):
            # meta files are ignored
            # FIXME: can this be removed
            continue
        elif filename.endswith('.meta'):
            # meta files are ignored
            continue
        else:
            full_dst = os.path.join(dst_path, filename)
            process_remain(app, full, full_dst)
    index += app['BLOB-FOOTER']
    index_file_path = os.path.join(dst_path, 'index.html')
    with open(index_file_path, 'w') as fd:
        fd.write(index)

def generate_all(app):
    for major_id in os.listdir(app['PATH-RAW']):
        src_path = os.path.join(app['PATH-RAW'], major_id)
        if not os.path.isdir(src_path):
            continue
        dst_path = os.path.join(app['PATH-GENERATE'], major_id)
        generate_major_page(app, major_id, src_path, dst_path)
    generate_index(app)

def generate_specific(app, value):
    type_, major_id = value
    src_path = os.path.join(app['PATH-RAW'], major_id)
    dst_path = os.path.join(app['PATH-GENERATE'], major_id)
    generate_major_page(app, major_id, src_path, dst_path)
    generate_index(app)

async def generator(app):
    while True:
        value = await app['QUEUE'].get()
        start = time.time()
        if not value:
            mode = 'all'
            generate_all(app)
        else:
            mode = 'specific,{}'.format(value[1])
            generate_specific(app, value)
        if app['DEBUG']:
            diff = time.time() - start
            msg = 'page generation completed (mode: {}) in {:.4f} seconds'.format(mode, diff)
            journal.log(app, msg)

TBL_HEAD = '''
<table class="table table-striped table-hover table-sm">
  <thead>
    <tr>
      <th scope="col">ID</th>
      <th scope="col">Last Modified</th>
      <th scope="col">First Modified</th>
      <th scope="col">Status</th>
      <th scope="col">Last Submitter</th>
    </tr>
  </thead>
  <tbody>
'''

TBL_FOOTER = '''
  </tbody>
</table>
'''
