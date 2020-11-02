# Copyright (C) 2020 Alex Verrico. All Rights Reserved


import sqlite3
import tkinter as tk
from queue import Queue
import time
import threading

# Initialize stuff

Basedir = ""
Db = "".join((Basedir, "main.sqlite"))
dbOperations = Queue(maxsize=0)


# Declare Functions

def add_entry(e_name=None, e_origin=None, e_retrieval_date=None, e_location=None, e_path=None, e_tags=None, _id=None):
    if not e_name:
        e_name = "unnamed"
    if not e_origin:
        e_origin = "unknown"
    if not e_retrieval_date:
        e_retrieval_date = "unknown"
    if not e_location:
        e_location = "unknown"
    if not e_path:
        e_path = "unknown"
    if not e_tags:
        e_tags = "unknown"

    if _id:
        print(_id)
        pass
    else:
        e_name = str(e_name)
        e_origin = str(e_origin)
        e_retrieval_date = str(e_retrieval_date)
        e_location = str(e_location)
        e_path = str(e_path)
        e_tags = str(e_tags).split(" ")
        print(e_tags)
        con = sqlite3.connect(Db)
        cur = con.cursor()
        # values = id,name,origin,retrieval_date,location,path,tags
        cur.execute("SELECT _contents FROM misc_stuff WHERE id = '000001'")
        _id = int(cur.fetchone()[0]) + 1
        _id = str(_id)
        _id = _id.zfill(6)
        print(_id)
        id_update_statement = "UPDATE misc_stuff SET _contents = ? WHERE id = '000001'"
        cur.execute(id_update_statement, (_id,))
        insert_statement = 'INSERT INTO entries values(?, ?, ?, ?, ?, ?, ?)'
        _e_tags = e_tags[0]
        for i in range(1, len(e_tags)):
            _e_tags = "".join((_e_tags, " ", e_tags[i]))
        cur.execute(insert_statement, (str(_id), e_name, e_origin, e_retrieval_date, e_location, e_path, _e_tags,))
        con.commit()
        return True


def run_queue():
    while True:
        if dbOperations.empty() is False:
            print(dbOperations.get()['action'])
        else:
            time.sleep(0.1)


# Run functions

# Start dbOperations Queue
t = threading.Timer(0, run_queue)
t.start()

# add_entry()

dbOperations.put({'action': 'update',
                  'dbPath': 'main.sqlite',
                  'table': 'test1',
                  'column': 'test2',
                  'columnValue': 'test3',
                  })

window = tk.Tk()
greeting = tk.Label(text="Hello, Tkinter")
greeting.pack()
button = tk.Button(
    text="Click me!",
    width=25,
    height=5,
    bg="blue",
    fg="yellow",
)
button.pack()
entry = tk.Entry(fg="yellow", bg="blue", width=50)
entry.pack()
window.mainloop()
