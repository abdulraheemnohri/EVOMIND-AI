import sqlite3,threading
SCHEMA="""PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY,created_at TEXT DEFAULT CURRENT_TIMESTAMP,role TEXT,content TEXT,runtime TEXT DEFAULT '',feedback INTEGER);
CREATE TABLE IF NOT EXISTS memories(id INTEGER PRIMARY KEY,content TEXT UNIQUE,source TEXT,status TEXT DEFAULT 'approved',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS skills(id INTEGER PRIMARY KEY,name TEXT UNIQUE,description TEXT,trigger_text TEXT,action TEXT,enabled INTEGER DEFAULT 1,uses INTEGER DEFAULT 0,positive INTEGER DEFAULT 0,negative INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS goals(id INTEGER PRIMARY KEY,title TEXT,details TEXT DEFAULT '',status TEXT DEFAULT 'open',progress TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,kind TEXT,detail TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY,title TEXT NOT NULL,description TEXT DEFAULT '',status TEXT DEFAULT 'pending',result TEXT DEFAULT '',created_at TEXT DEFAULT CURRENT_TIMESTAMP,updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS agent_runs(id INTEGER PRIMARY KEY,agent TEXT NOT NULL,input TEXT NOT NULL,output TEXT DEFAULT '',status TEXT DEFAULT 'completed',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS app_settings(key TEXT PRIMARY KEY,value TEXT NOT NULL,updated_at TEXT DEFAULT CURRENT_TIMESTAMP);"""
class Database:
    def __init__(self,path):
        self.path=str(path);self.lock=threading.RLock()
        with self.connect() as d:d.executescript(SCHEMA)
    def connect(self):
        d=sqlite3.connect(self.path,timeout=20,check_same_thread=False);d.row_factory=sqlite3.Row;return d
    def execute(self,q,p=()):
        with self.lock,self.connect() as d:
            c=d.execute(q,p);return c.lastrowid,c.rowcount
    def rows(self,q,p=()):
        with self.lock,self.connect() as d:return [dict(x) for x in d.execute(q,p).fetchall()]
    def one(self,q,p=()):
        with self.lock,self.connect() as d:
            x=d.execute(q,p).fetchone();return dict(x) if x else None
    def count(self,t):
        if t not in {"messages","memories","skills","goals","events","tasks","agent_runs"}:raise ValueError("bad table")
        return self.one("SELECT COUNT(*) n FROM "+t)["n"]
