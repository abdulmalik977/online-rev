"""Private SQLite state. No customer data belongs in the Git working tree."""
from contextlib import contextmanager
import csv
import json
import re
from pathlib import Path
import sqlite3
import threading

from .calendar import stamp, instant, next_business_day
from .rules import normalize, SHARED


class Store:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, isolation_level=None, timeout=10, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self.conn.executescript('''
          PRAGMA foreign_keys=ON;
          PRAGMA journal_mode=WAL;
          PRAGMA synchronous=FULL;
          CREATE TABLE IF NOT EXISTS prospects(id TEXT PRIMARY KEY,email TEXT NOT NULL,data TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS sends(id INTEGER PRIMARY KEY,prospect_id TEXT NOT NULL REFERENCES prospects(id),
            email_no TEXT NOT NULL,kind TEXT NOT NULL,mailbox TEXT NOT NULL,message_id TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL,created TEXT NOT NULL,updated TEXT NOT NULL,attempt INTEGER NOT NULL,
            template TEXT,body TEXT,accepted_at TEXT,not_before TEXT);
          CREATE INDEX IF NOT EXISTS send_job ON sends(prospect_id,email_no);
          CREATE TABLE IF NOT EXISTS inbound(id TEXT PRIMARY KEY,prospect_id TEXT,at TEXT,kind TEXT,action TEXT);
          CREATE TABLE IF NOT EXISTS suppression(key TEXT,kind TEXT,reasons TEXT,added_at TEXT,source_message_id TEXT,
            PRIMARY KEY(key,kind));
          CREATE TABLE IF NOT EXISTS queue(id INTEGER PRIMARY KEY,prospect_id TEXT,source TEXT,class TEXT,
            created TEXT,due TEXT,draft TEXT,resolved INTEGER DEFAULT 0,UNIQUE(source,class));
          CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY,prospect_id TEXT,at TEXT,refunded INTEGER DEFAULT 0);
          CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,mailbox TEXT,kind TEXT,at TEXT,recipient TEXT,send_id INTEGER);
          CREATE TABLE IF NOT EXISTS mailboxes(id TEXT PRIMARY KEY,first_send TEXT,pause_until TEXT,
            disabled INTEGER DEFAULT 0,pauses TEXT DEFAULT '[]');
          CREATE TABLE IF NOT EXISTS views(id TEXT PRIMARY KEY,prospect_id TEXT,at TEXT,excluded INTEGER);
          CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,at TEXT,action TEXT,detail TEXT);
        ''')

    def close(self):
        self.conn.close()

    @contextmanager
    def transaction(self):
        with self.lock:
            nested = self.conn.in_transaction
            if not nested:
                self.conn.execute('BEGIN IMMEDIATE')
            try:
                yield self.conn
                if not nested:
                    self.conn.commit()
            except BaseException:
                if not nested:
                    self.conn.rollback()
                raise

    def add(self, prospect):
        value = dict(prospect)
        if not re.fullmatch(r'[a-z0-9-]+',value['id']):
            raise ValueError('Prospect ID must be a safe stable slug')
        value['email'] = normalize(value['email'])
        value.setdefault('state','queued')
        with self.transaction() as conn:
            conn.execute('INSERT INTO prospects VALUES(?,?,?)', (value['id'],value['email'],json.dumps(value)))

    def get(self, ident):
        row = self.conn.execute('SELECT data FROM prospects WHERE id=?',(ident,)).fetchone()
        if not row:
            raise KeyError(ident)
        return json.loads(row[0])

    def save(self, prospect):
        self.conn.execute('UPDATE prospects SET data=?,email=? WHERE id=?',
                          (json.dumps(prospect),prospect['email'],prospect['id']))

    def by_email(self, address):
        row = self.conn.execute('SELECT id FROM prospects WHERE email=?',(normalize(address),)).fetchone()
        return self.get(row[0]) if row else None

    def suppress(self, address, reason, at, source, shared=SHARED, business=None):
        address = normalize(address)
        domain = address.rsplit('@',1)[1]
        keys = [(address,'email')]
        if reason == 'unsubscribe' and business:
            keys.extend((normalize(a),'email') for a in business.get('emails',[]))
        if reason in {'legal','negative','complaint'} and domain not in shared:
            keys.append((domain,'domain'))
        for key, kind in keys:
            old = self.conn.execute('SELECT * FROM suppression WHERE key=? AND kind=?',(key,kind)).fetchone()
            if old:
                reasons = sorted(set(json.loads(old['reasons'])) | {reason})
                self.conn.execute('UPDATE suppression SET reasons=? WHERE key=? AND kind=?',(json.dumps(reasons),key,kind))
            else:
                self.conn.execute('INSERT INTO suppression VALUES(?,?,?,?,?)',(key,kind,json.dumps([reason]),stamp(at),source))

    def suppressed(self, address):
        address = normalize(address)
        domain = address.rsplit('@',1)[1]
        for row in self.conn.execute('SELECT key,kind FROM suppression'):
            if (row['kind']=='email' and row['key']==address) or (row['kind']=='domain' and (domain==row['key'] or domain.endswith('.'+row['key']))):
                return True
        return False

    def enqueue(self, prospect, source, kind, at, draft, holidays=()):
        self.conn.execute('INSERT OR IGNORE INTO queue(prospect_id,source,class,created,due,draft) VALUES(?,?,?,?,?,?)',
                          (prospect,source,kind,stamp(at),self.owner_due(at,holidays),draft))

    @staticmethod
    def owner_due(received_at, holidays=()):
        # A7: all owner queues start at receipt, never at payment/confirmation.
        return stamp(next_business_day(received_at,holidays))

    @staticmethod
    def queue_ident(row):
        if row['class']=='unknown_send':
            return f"Q-{row['prospect_id']}-unknown-send"
        return f"Q-{row['prospect_id'] or 'unknown'}-{row['id']}"

    def paid(self, order_id, prospect_id, at):
        with self.transaction() as conn:
            inserted = conn.execute('INSERT OR IGNORE INTO orders(id,prospect_id,at) VALUES(?,?,?)',(order_id,prospect_id,stamp(at))).rowcount
            existing = conn.execute('SELECT prospect_id FROM orders WHERE id=?',(order_id,)).fetchone()
            if existing[0] != prospect_id:
                raise ValueError('Order ID belongs to a different prospect')
            p = self.get(prospect_id)
            if p['state'] not in {'suppressed','paid','expired'}:
                p['state']='paid'
            self.save(p)
            self.suppress(p['email'],'customer',at,order_id)
            return bool(inserted)

    def export_suppression(self, path):
        with Path(path).open('w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f); writer.writerow(['key','kind','reason','added_at','source_message_id'])
            for row in self.conn.execute('SELECT * FROM suppression ORDER BY kind,key'):
                writer.writerow([row['key'],row['kind'],';'.join(json.loads(row['reasons'])),row['added_at'],row['source_message_id']])

    def project_queue(self, root, at):
        from scripts.common import locked
        with locked(Path(root)), self.lock:
            return self._project_queue(root,at)

    def _project_queue(self, root, at):
        """Recoverable/idempotent Markdown projection; root must be a private data root."""
        root=Path(root); (root/'sales/queue').mkdir(parents=True,exist_ok=True)
        (root/'approvals').mkdir(exist_ok=True)
        pending=root/'approvals/pending.md'
        previous=pending.read_text(encoding='utf-8') if pending.exists() else '# Pending owner inputs\n'
        critical=[]
        for row in self.conn.execute('SELECT * FROM queue ORDER BY id'):
            # IDs are database-generated; untrusted email cannot become a path.
            ident=self.queue_ident(row)
            safe_source=' '.join(row['source'].split())[:200]
            draft=root/'sales/queue'/f'{ident}.md'
            content=f"# {ident}\n\nClass: {row['class']}\nDue: {row['due']}\nThread: {safe_source}\n\nDraft (not sent):\n{row['draft']}\n"
            temp=draft.with_suffix('.tmp'); temp.write_text(content,encoding='utf-8'); temp.replace(draft)
            marker='x' if row['resolved'] else ' '
            line=f"- [{marker}] {ident} | {row['created']} | {row['class']}; thread {safe_source}; draft in sales/queue/{ident}.md"
            lines=previous.splitlines()
            owned=[i for i,text in enumerate(lines) if text.startswith((f'- [ ] {ident} |',f'- [x] {ident} |'))]
            if owned:
                lines[owned[0]]=line
            else:
                lines.append(line)
            previous='\n'.join(lines)+'\n'
            if not row['resolved'] and row['due'] and instant(at)>instant(row['due']):
                critical.append(ident)
        temp=pending.with_suffix('.tmp'); temp.write_text(previous,encoding='utf-8'); temp.replace(pending)
        return critical
