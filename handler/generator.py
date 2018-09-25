import os
import time
import markdown
import shutil
import datetime
import json

from handler.upload import PATH_META_SELF

#= '.meta/self'
PATH_META_FOREIGN = '.meta/foreign'

extensions = ['markdown.extensions.tables', 'fenced_code', 'nl2br']

def hippid_date_parse(string):
    return datetime.datetime.strptime(string, '%Y-%m-%dT%H:%M:%S.%f')

def human_date_delta(date):
    diff = datetime.datetime.utcnow() - date
    s = diff.seconds
    if diff.days > 7 or diff.days < 0:
        return d.strftime('%d %b %y')
    elif diff.days == 1:
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
        return '{} minutes ago'.format(s / 60)
    elif s < 7200:
        return '1 hour ago'
    else:
        return '{} hours ago'.format(s / 3600)

def create_id_insert(object_list, new):
    if len(object_list) <= 0:
        object_list.append(new)
        return
    for num, object_ in enumerate(object_list):
        if object_.modified_last <= new.modified_last:
            object_list.insert(num, new)
            return
    object_list.append(new)

def create_id_list(app):
    ''' return a sorted object based list of id's with meta-data'''
    ret_list = list()
    for major_id in os.listdir(app['PATH-DB']):
        full = os.path.join(app['PATH-DB'], major_id)
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
        create_id_insert(ret_list, ret)
    return ret_list


def generate_index_table(app):
    tbl = TBL_HEAD
    create_id_list(app)
    for entity in create_id_list(app):
        tbl += '<tr>'
        tbl += '<td><a href="❤️/' + entity.id + '/">' + entity.id + '</a></td>'
        tbl += '<td>' + human_date_delta(entity.modified_last) + ' (' + entity.modified_last.strftime('%d %B %Y') + ')</td>'
        tbl += '<td>' + entity.modified_first.strftime('%d %B %Y') + '</td>'
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

def process_md(app, major_id, md_name, path, full):
    cnd = ''
    with open(full, 'r') as fd:
        cnt = fd.read()
    html = markdown.markdown(cnt, extensions=extensions)
    return html

def process_remain(app, major_id, filename_name, path, full, index_path):
    """ simple copy the rest """
    dst = os.path.join(index_path, filename_name)
    shutil.copyfile(full, dst)

def generate_major_page(app, major_id, path):
    index_path = os.path.join(app['PATH-GENERATE'], major_id)
    os.makedirs(index_path, exist_ok=True)
    index = app['BLOB-HEADER']
    for filename in sorted(os.listdir(path)):
        full = os.path.join(path, filename)
        if filename.endswith('.md'):
            index += process_md(app, major_id, filename, path, full)
        elif filename.startswith('.'):
            # meta files are ignored
            continue
        else:
            process_remain(app, major_id, filename, path, full, index_path)
    index += app['BLOB-FOOTER']
    index_file_path = os.path.join(index_path, 'index.html')
    with open(index_file_path, 'w') as fd:
        fd.write(index)

def generate_major_pages(app):
    for major_id in os.listdir(app['PATH-DB']):
        full = os.path.join(app['PATH-DB'], major_id)
        if not os.path.isdir(full):
            continue
        generate_major_page(app, major_id, full)

def generate_all(app):
    print('generate new, full pages for all pages')
    generate_major_pages(app)
    generate_index(app)

def generate_specific(app, value):
    type_, major_id = value
    generate_all(app)

async def generator(app):
    while True:
        value = await app['QUEUE'].get()
        if not value:
            generate_all(app)
        else:
            generate_specific(app, value)

TBL_HEAD = '''
<table class="table table-striped table-hover table-sm">
  <thead>
    <tr>
      <th scope="col">ID</th>
      <th scope="col">Last Modified</th>
      <th scope="col">First Modified</th>
      <th scope="col">Last Submitter</th>
    </tr>
  </thead>
  <tbody>
'''

TBL_FOOTER = '''
  </tbody>
</table>
'''
