# Copyright (C) 2020 Alex Verrico. All Rights Reserved
# For licensing enquiries please contact Alex Verrico (contact@alexverrico.com)


import sqlite3
# import tkinter as tk
from queue import Queue
# import time
from threading import Timer
import os
# import datetime
import flask
from dotenv import load_dotenv
import json

# Initialize stuff

load_dotenv()
Basedir = os.getenv("BASEDIR")
dbPath = "".join((Basedir, "main.sqlite"))
dbOperations = Queue(maxsize=0)

app = flask.Flask(__name__)

# Declare Functions


# def add_entry(e_name=None, e_origin=None, e_retrieval_date=None, e_location=None, e_path=None, e_tags=None, _id=None):
#     if not e_name:
#         e_name = "unnamed"
#     if not e_origin:
#         e_origin = "unknown"
#     if not e_retrieval_date:
#         e_retrieval_date = "unknown"
#     if not e_location:
#         e_location = "unknown"
#     if not e_path:
#         e_path = "unknown"
#     if not e_tags:
#         e_tags = "unknown"
#
#     if _id:
#         print(_id)
#         pass
#     else:
#         e_name = str(e_name)
#         e_origin = str(e_origin)
#         e_retrieval_date = str(e_retrieval_date)
#         e_location = str(e_location)
#         e_path = str(e_path)
#         e_tags = str(e_tags).split(" ")
#         print(e_tags)
#         con = sqlite3.connect(dbPath)
#         cur = con.cursor()
#         # values = id,name,origin,retrieval_date,location,path,tags
#         cur.execute("SELECT _contents FROM misc_stuff WHERE id = '000001'")
#         _id = int(cur.fetchone()[0]) + 1
#         _id = str(_id)
#         _id = _id.zfill(6)
#         print(_id)
#         id_update_statement = "UPDATE misc_stuff SET _contents = ? WHERE id = '000001'"
#         cur.execute(id_update_statement, (_id,))
#         insert_statement = 'INSERT INTO entries values(?, ?, ?, ?, ?, ?, ?)'
#         _e_tags = e_tags[0]
#         for i in range(1, len(e_tags)):
#             _e_tags = "".join((_e_tags, " ", e_tags[i]))
#         cur.execute(insert_statement, (str(_id), e_name, e_origin, e_retrieval_date, e_location, e_path, _e_tags,))
#         con.commit()
#         return True


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
        with open(f'html/templates/{template["file"]}', 'r') as f:
            page = page.replace(f'%%%{template["string"]}%%%', f.read())
    return page


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
    page = insert_templates('html/pages/home.html')
    return page, 200


@app.route('/entry_by_id/', methods=['GET'])
def entry_by_id():
    page = insert_templates('html/pages/entry_by_id.html')
    return page, 200


@app.route('/find_by_name/', methods=['GET'])
def find_by_name():
    page = insert_templates('html/pages/find_by_name.html')
    return page, 200


@app.route('/find_by_tag/', methods=['GET'])
def find_by_tag():
    page = insert_templates('html/pages/find_by_tag.html')
    return page, 200


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


# Run functions

t = Timer(0, run_queue)
t.start()  # Start dbOperations Queue

app.run('0.0.0.0', 5515)
