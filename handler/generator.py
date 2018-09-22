import os
import time
import markdown

extensions = ['markdown.extensions.tables']


def generate_index_table(app):
    tbl = ''
    for id_ in os.listdir(app['PATH-DB']):
        full = os.path.join(app['PATH-DB'], id_)
        if not os.path.isdir(full):
            continue
        tbl += '<a href="id/' + id_ + '">' + id_ + '</a>'
    return tbl

def generate_index(app):
    new_index = app['BLOB-HEADER']
    new_index += generate_index_table(app)
    new_index += app['BLOB-FOOTER']
    path = os.path.join(app['PATH-GENERATE'], 'index.html')
    with open(path, 'w') as fd:
        fd.write(new_index)

def process_md(app, id_, md_name, path, full):
    cnd = ''
    with open(full, 'r') as fd:
        cnt = fd.read()
    html = markdown.markdown(cnt, extensions=extensions)
    return html

def generate_major_page(app, id_, path):
    index = app['BLOB-HEADER']
    for filename in sorted(os.listdir(path)):
        full = os.path.join(path, filename)
        if filename.endswith('.md'):
            index += process_md(app, id_, filename, path, full)
    index += app['BLOB-FOOTER']

    index_path = os.path.join(app['PATH-GENERATE'], 'id', id_)
    os.makedirs(index_path, exist_ok=True)
    index_file_path = os.path.join(index_path, 'index.html')
    with open(index_file_path, 'w') as fd:
        fd.write(index)

def generate_major_pages(app):
    for id_ in os.listdir(app['PATH-DB']):
        full = os.path.join(app['PATH-DB'], id_)
        if not os.path.isdir(full):
            continue
        generate_major_page(app, id_, full)

def generate_all(app):
    generate_major_pages(app)
    generate_index(app)

def generate_specific(app, value):
    type_, id_ = value
    generate_all(app)

async def generator(app):
    while True:
        value = await app['QUEUE'].get()
        if not value:
            generate_all(app)
        else:
            generate_specific(app, value)
