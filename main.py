#! /usr/bin/python3

# Copyright (C) 2020 Alex Verrico. All Rights Reserved
# For licensing enquiries please contact Alex Verrico (contact@alexverrico.com)


import sqlite3
from queue import Queue
from threading import Timer
import os
import flask
from dotenv import load_dotenv
import json
import shutil


# Initialize stuff
load_dotenv()
Basedir = os.getenv("BASEDIR")
dbPath = "".join((Basedir, "main.sqlite"))
dbOperations = Queue(maxsize=0)

app = flask.Flask(__name__)
port = os.getenv("PORT")
# app.config["DEBUG"] = True


# Declare Functions


def run_queue():
    while True:
        if dbOperations.empty() is False:
            x = dbOperations.get()
            data = x['data']
            if x['action'] == 'update' and x['scope'] == 'row':
                con = sqlite3.connect(x['dbPath'])
                cur = con.cursor()
                update_statement = "UPDATE %s SET name = ?, origin = ?, retrieval_date = ?, location = ?, path = ?, tags = ? WHERE %s = ?" % (x['table'], x['column'])
                cur.execute(update_statement, (data['name'],
                                               data['origin'],
                                               data['retrieval'],
                                               data['location'],
                                               data['path'],
                                               data['tags'],
                                               x['columnValue']))
                con.commit()
                con.close()
            if x['action'] == 'create' and x['scope'] == 'row':
                con = sqlite3.connect(x['dbPath'])
                cur = con.cursor()
                cur.execute("SELECT _contents FROM misc_stuff WHERE id = '000001'")
                _id = int(cur.fetchone()[0]) + 1
                cur.execute("UPDATE misc_stuff SET _contents = '%s' WHERE id = '000001'" % str(_id).zfill(10))
                con.commit()
                create_statement = "INSERT INTO %s VALUES (?, ?, ?, ?, ?, ?, ?)" % x['table']
                cur.execute(create_statement, (str(_id).zfill(10),
                                               data['name'],
                                               data['origin'],
                                               data['retrieval'],
                                               data['location'],
                                               data['path'],
                                               data['tags']))
                con.commit()
                con.close()


def insert_templates(page):
    with open(page, 'r') as f:
        page = f.read()
    template_list = [{'file': 'head.html', 'string': 'head'},
                     {'file': 'nav.html', 'string': 'nav'},
                     {'file': 'footer.html', 'string': 'footer'},
                     {'file': 'core.html', 'string': 'corejs'}]
    for template in template_list:
        _path = ''.join((Basedir, f'html/templates/{template["file"]}'))
        with open(_path, 'r') as f:
            page = page.replace(f'%%%{template["string"]}%%%', f.read())
    return page


def recursive_listdir(path):
    out = []
    for dirpath, dirnames, filenames in os.walk(path):
        for file in filenames:
            if file.endswith('.html'):
                out.append("/".join([dirpath, file]))
    return out


def build_static_pages():
    pages_dir = ''.join((Basedir, 'html/pages'))
    built_dir = ''.join((Basedir, 'built'))
    if os.path.exists(built_dir):
        shutil.rmtree(built_dir)
    os.mkdir(built_dir)
    filelist = recursive_listdir(pages_dir)
    out = []
    for file in filelist:
        file = file[len(pages_dir):]
        while file.startswith('/'):
            file = file[1:]
        while file.startswith('\\'):
            file = file[1:]
        out.append(file)
    for file in out:
        page = insert_templates(''.join((pages_dir, '/', file)))
        path = file.rsplit('/', 1)
        path = ''.join((built_dir, '/', path[0]))
        if not path.endswith('.html'):
            if not os.path.exists(path):
                os.makedirs(path)
        with open(''.join((built_dir, '/', file)), 'w') as f:
            f.write(page)
    return True


def auth(_uid, _auth, _type='system'):
    _connection = sqlite3.connect(dbPath)
    _cursor = _connection.cursor()
    _auth_cmd = "SELECT password FROM auth WHERE id = ?"
    _temp = _cursor.execute(_auth_cmd, (str(_uid),)).fetchone()
    if str(_auth) == str(_temp[0]):
        return True
    else:
        return False


# Flask stuff
# First we declare the normal paths:
@app.route('/', methods=['GET'])
def home():
    _dir = ''.join((Basedir, 'built'))
    return flask.send_from_directory(_dir, 'index.html')


# Then we declare the api paths:
@app.route('/api/v1/seek/by_id', methods=['GET'])
def seek_by_id():
    if 'uid' not in flask.request.args or 'auth' not in flask.request.args or 'id' not in flask.request.args:
        return '', 400
    else:
        _uid = str(flask.request.args['uid'])
        _auth = str(flask.request.args['auth'])
        _id = str(flask.request.args['id'])
    if auth(_uid, _auth) is False:
        return '', 400
    select_statement = "SELECT * FROM entries WHERE id = ?"
    con = sqlite3.connect(dbPath)
    cur = con.cursor()
    cur.execute(select_statement, (_id,))
    x = cur.fetchone()
    con.close()
    if x is None:
        return flask.jsonify({'name': 'Invalid ID', 'id': _id}), 200
    out = dict()
    out['id'] = x[0]
    out['name'] = x[1]
    out['origin'] = x[2]
    out['retrieval_date'] = x[3]
    out['location'] = x[4]
    out['path'] = x[5]
    out['tags'] = x[6]
    return flask.jsonify(out), 200


@app.route('/api/v1/seek/by_name', methods=['GET'])
def seek_by_name():
    if 'uid' not in flask.request.args or 'auth' not in flask.request.args or 'name' not in flask.request.args:
        return '', 400
    else:
        _uid = str(flask.request.args['uid'])
        _auth = str(flask.request.args['auth'])
        _name = str(flask.request.args['name'])
    if auth(_uid, _auth) is False:
        return '', 400
    _name = _name.replace("!", "!!").replace("%", "!%").replace("_", "!_").replace("[", "![")
    select_statement = "SELECT * FROM entries WHERE name LIKE ? ESCAPE '!'"
    con = sqlite3.connect(dbPath)
    cur = con.cursor()
    _name = "".join(("%", _name, "%"))
    cur.execute(select_statement, (_name,))
    db_out = cur.fetchall()
    con.close()
    if db_out is None:
        return flask.jsonify({'name': _name, 'id': "no_results"}), 200
    out = list()
    for x in db_out:
        _temp = dict()
        _temp['id'] = x[0]
        _temp['name'] = x[1]
        _temp['origin'] = x[2]
        _temp['retrieval_date'] = x[3]
        _temp['location'] = x[4]
        _temp['path'] = x[5]
        _temp['tags'] = x[6]
        out.append(_temp)
    return flask.jsonify(out), 200


@app.route('/api/v1/seek/by_tag', methods=['GET'])
def seek_by_tag():
    if 'uid' not in flask.request.args or 'auth' not in flask.request.args or 'tag' not in flask.request.args:
        return '', 400
    else:
        _uid = str(flask.request.args['uid'])
        _auth = str(flask.request.args['auth'])
        _tag = str(flask.request.args['tag'])
    if auth(_uid, _auth) is False:
        return '', 400
    _tag = _tag.replace("!", "!!").replace("%", "!%").replace("_", "!_").replace("[", "![")
    select_statement = "SELECT * FROM entries WHERE tags LIKE ? ESCAPE '!'"
    con = sqlite3.connect(dbPath)
    cur = con.cursor()
    _tag = "".join(("%", _tag, "%"))
    cur.execute(select_statement, (_tag,))
    db_out = cur.fetchall()
    con.close()
    if db_out is None:
        return flask.jsonify({'tag': _tag, 'id': "no_results"}), 200
    out = list()
    for x in db_out:
        _temp = dict()
        _temp['id'] = x[0]
        _temp['name'] = x[1]
        _temp['origin'] = x[2]
        _temp['retrieval_date'] = x[3]
        _temp['location'] = x[4]
        _temp['path'] = x[5]
        _temp['tags'] = x[6]
        out.append(_temp)
    return flask.jsonify(out), 200


@app.route('/api/v1/update/by_id', methods=['POST'])
def update_by_id():
    if 'uid' not in flask.request.values or 'auth' not in flask.request.values or 'id' not in flask.request.values or 'data' not in flask.request.values:
        return '', 400
    else:
        _uid = str(flask.request.values['uid'])
        _auth = str(flask.request.values['auth'])
        _id = str(flask.request.values['id'])
        _data = json.loads(flask.request.values['data'])
    if auth(_uid, _auth) is False:
        return '', 400
    con = sqlite3.connect(dbPath)
    cur = con.cursor()
    select_statement = "SELECT * FROM entries WHERE id = ?"
    cur.execute(select_statement, [_id])
    x = cur.fetchone()
    db_data = dict()
    if x is None:
        db_data['action'] = 'create'
    else:
        db_data['action'] = 'update'
    db_data['scope'] = 'row'
    db_data['dbPath'] = dbPath
    db_data['table'] = 'entries'
    db_data['column'] = 'id'
    db_data['columnValue'] = _id
    db_data['data'] = _data
    dbOperations.put(db_data)
    return '', 200


# And finally we create a catch-all route to serve the pre-built pages
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if '..' in str(path):
        return '', 404
    try:
        x = path.split('.')[1]
        x = True
    except IndexError:
        path = ''.join((path, '/'))
        x = False
    if path.endswith('/'):
        path = ''.join((path, 'index.html'))
    _dir = ''.join((Basedir, 'built'))
    return flask.send_from_directory(_dir, path)


# Run functions

t = Timer(0, run_queue)
t.start()  # Start dbOperations Queue

print("Building pages....")
build_static_pages()
print("Built pages.")

app.run('0.0.0.0', port)
