"""Durable process events and signed heartbeats; no process protection claims."""
import atexit
import getpass
import json
import logging
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager

LOGGER=logging.getLogger(__name__)


class EventOutbox:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock()
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)')

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=2)
        try:
            with db:yield db
        finally:db.close()

    def add(self,kind,details=None):
        with self.lock,self.connect() as db:return self.insert(db,kind,details)

    def insert(self,db,kind,details=None):
        event={'id':str(uuid.uuid4()),'kind':kind,'reported_at':datetime.now(timezone.utc).isoformat(),'details':details or {}}
        db.execute('INSERT INTO events VALUES (?,?)',(event['id'],json.dumps(event)))
        return event

    def begin(self):
        with self.lock,self.connect() as db:
            row=db.execute("SELECT value FROM meta WHERE key='process'").fetchone()
            previous=json.loads(row[0]) if row else None
            db.execute("INSERT OR REPLACE INTO meta VALUES ('process',?)",(json.dumps({'running':True,'pid':os.getpid()}),))
            if previous and previous.get('running'):
                self.insert(db,'previous_exit_unconfirmed',{'previous_pid':previous.get('pid'),'reason':'Toza yopilish qaydi yo‘q: xato, majburiy yopilish yoki elektr uzilishi mumkin'})
            if previous:self.insert(db,'agent_restarted',{'pid':os.getpid(),'reason':'Yangi agent jarayoni kuzatildi'})
            self.insert(db,'agent_started',{'pid':os.getpid(),'os_user':getpass.getuser()})

    def finish(self,reason):
        with self.lock,self.connect() as db:
            row=db.execute("SELECT value FROM meta WHERE key='process'").fetchone()
            if not row or not json.loads(row[0]).get('running'):return
            db.execute("INSERT OR REPLACE INTO meta VALUES ('process',?)",(json.dumps({'running':False,'pid':os.getpid()}),))
            self.insert(db,'agent_exited',{'pid':os.getpid(),'reason':reason})

    def pending(self):
        with self.lock,self.connect() as db:return [json.loads(row[0]) for row in db.execute('SELECT payload FROM events ORDER BY rowid LIMIT 50')]

    def acknowledge(self,ids):
        if not isinstance(ids,list):return
        with self.lock,self.connect() as db:
            db.executemany('DELETE FROM events WHERE id=?',[(value,) for value in ids if isinstance(value,str)])


class Reporter:
    def __init__(self,queue,send):
        self.queue,self.send=queue,send
        self.stopping=threading.Event();self.thread=None
        self.send_lock=threading.Lock()

    def flush(self):
        try:
            with self.send_lock:
                batch=self.queue.pending()
                result=self.send({'events':batch,'state':'stopped' if self.stopping.is_set() else 'running'})
                if isinstance(result,dict):
                    accepted=set(result.get('accepted',[])) if isinstance(result.get('accepted'),list) else set()
                    self.queue.acknowledge([event['id'] for event in batch if event['id'] in accepted])
        except Exception as error:
            LOGGER.warning('Agent telemetry deferred (%s)',type(error).__name__)

    def start(self):
        def loop():
            self.flush()
            while not self.stopping.wait(30):self.flush()
            self.flush()
        self.thread=threading.Thread(target=loop,daemon=True,name='ADAuthTelemetry');self.thread.start()

    def stop(self,reason='window_closed'):
        if self.stopping.is_set():return
        try:self.queue.finish(reason)
        except Exception as error:LOGGER.warning('Agent exit journal unavailable (%s)',type(error).__name__)
        self.stopping.set()
        if self.thread and self.thread is not threading.current_thread():self.thread.join(3)


_reporter=None


def start_telemetry():
    global _reporter
    try:
        from api.client import get_default_client
        from core.config import DEVICE_UUID
        root=Path(os.environ['APPDATA'])/'ADBioGuard'
        queue=EventOutbox(root/'telemetry.sqlite3');queue.begin()
        client=get_default_client()
        _reporter=Reporter(queue,lambda payload:client.post('/api/agent/telemetry/',{'device_uuid':DEVICE_UUID,**payload},timeout=3))
        _reporter.start();atexit.register(stop_telemetry)
    except Exception as error:LOGGER.warning('Agent telemetry unavailable (%s)',type(error).__name__)


def stop_telemetry(reason='window_closed'):
    if _reporter:_reporter.stop(reason)
