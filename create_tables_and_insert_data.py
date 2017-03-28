import sqlite3
import csv
import pprint

#Create DB
sqlite_db = 'OSM_Project.sqlite'

#Create connection
conn = sqlite3.connect(sqlite_db)

#Create cursor
cur = conn.cursor()

#Create Tables
cur.execute('''CREATE TABLE nodes (
    id INTEGER PRIMARY KEY NOT NULL,
    lat REAL,
    lon REAL,
    user TEXT,
    uid INTEGER,
    version INTEGER,
    changeset INTEGER,
    timestamp TEXT
);''')

cur.execute('''CREATE TABLE nodes_tags (
    id INTEGER,
    key TEXT,
    value TEXT,
    type TEXT,
    FOREIGN KEY (id) REFERENCES nodes(id)
);''')

cur.execute('''CREATE TABLE ways (
    id INTEGER PRIMARY KEY NOT NULL,
    user TEXT,
    uid INTEGER,
    version TEXT,
    changeset INTEGER,
    timestamp TEXT
);''')

cur.execute('''CREATE TABLE ways_tags (
    id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    type TEXT,
    FOREIGN KEY (id) REFERENCES ways(id)
);''')

cur.execute('''CREATE TABLE ways_nodes (
    id INTEGER NOT NULL,
    node_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    FOREIGN KEY (id) REFERENCES ways(id),
    FOREIGN KEY (node_id) REFERENCES nodes(id)
);''')

#Create data for insertion
with open('nodes.csv','rb') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db_nodes = [(i['id'], i['lat'], i['lon'], i['user'].decode('utf-8'), i['uid'], i['version'], i['changeset'], i['timestamp']) for i in dr]
    
with open('nodes_tags.csv','rb') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db_nodes_tags = [(i['id'], i['key'].decode('utf-8'), i['value'].decode('utf-8'), i['type']) for i in dr]
    
with open('ways.csv','rb') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db_ways = [(i['id'], i['user'].decode('utf-8'), i['uid'], i['version'], i['changeset'], i['timestamp']) for i in dr]
    
with open('ways_tags.csv','rb') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db_ways_tags = [(i['id'], i['key'], i['value'].decode('utf-8'), i['type']) for i in dr]
    
with open('ways_nodes.csv','rb') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db_ways_nodes = [(i['id'], i['node_id'], i['position']) for i in dr]

#Insert data
cur.executemany('''Insert into nodes (id, lat, lon, user, uid, version, changeset, timestamp)
values (?,?,?,?,?,?,?,?);''', to_db_nodes)

cur.executemany('''Insert into nodes_tags (id, key, value, type)
values (?,?,?,?);''', to_db_nodes_tags)

cur.executemany('''Insert into ways (id, user, uid, version, changeset, timestamp)
values (?,?,?,?,?,?);''', to_db_ways)

cur.executemany('''Insert into ways_tags (id, key, value, type)
values (?,?,?,?);''', to_db_ways_tags)

cur.executemany('''Insert into ways_nodes (id, node_id, position)
values (?,?,?);''', to_db_ways_nodes)

#Commit changes
conn.commit()

#Close connection
conn.close()