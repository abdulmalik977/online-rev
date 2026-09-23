"""Loopback-only customer enquiry form. The sales-page concept request is mailto."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from html import escape
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import re
import secrets
from urllib.parse import parse_qs, urlsplit

from sender.calendar import instant, stamp
from .flow import Orders, SLUG


def local_server(store,port=0,clock=lambda:datetime.now(timezone.utc)):
    root,secret,config=store.root,store.secret,dict(store.config)
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self,*args): pass

        def respond(self,status,text):
            payload=text.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Length',str(len(payload)))
            self.send_header('Cache-Control','no-store')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers(); self.wfile.write(payload)

        def identity(self):
            return hmac.new(secret,self.client_address[0].encode(),sha256).hexdigest()

        def token(self,slug,ts,ident):
            return hmac.new(secret,(slug+'|'+str(ts)+'|'+ident+'|'+self.identity()).encode(),sha256).hexdigest()

        def customer(self,db):
            match=re.fullmatch(r'/enquiry/([a-z0-9][a-z0-9-]{1,100})',urlsplit(self.path).path)
            if not match: raise ValueError('Unknown page')
            slug=match.group(1)
            row=db.db.execute("SELECT * FROM orders WHERE slug=? AND status IN ('live','cancel_pending')",(slug,)).fetchone()
            if not row: raise ValueError('Customer site is not live')
            f=db.fulfilment(row['id'])
            if f['cancel_at'] and instant(clock())>=instant(f['cancel_at']): raise ValueError('Service ended')
            return slug

        def do_GET(self):
            db=Orders(root,secret,config)
            try:
                slug=self.customer(db); ts=int(instant(clock()).timestamp()); ident=secrets.token_hex(16)
                token=self.token(slug,ts,ident)
                name=db.db.execute('SELECT id FROM orders WHERE slug=?',(slug,)).fetchone()[0]
                business=escape(db.record(name)['business'])
                self.respond(200,f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Contact {business}</title><main><h1>Contact {business}</h1><form method="post"><input type="hidden" name="id" value="{ident}"><input type="hidden" name="timestamp" value="{ts}"><input type="hidden" name="token" value="{token}"><label>Name <input name="name" maxlength="120" required></label><br><label>Email <input type="email" name="email" maxlength="254" required></label><br><label>Message <textarea name="message" maxlength="3000" required></textarea></label><p>Your details will be forwarded to this business. Do not include sensitive information.</p><button>Send enquiry</button></form></main></html>''')
            except ValueError: self.respond(404,'Not found')
            finally: db.close()

        def do_POST(self):
            if self.headers.get('Origin')!=self.server.allowed_origin:
                self.respond(403,'Origin refused'); return
            try:
                if self.headers.get('Transfer-Encoding') or self.headers.get_content_type()!='application/x-www-form-urlencoded':
                    raise ValueError
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=8192:
                    self.respond(413,'Request too large'); return
                raw=self.rfile.read(length)
                if len(raw)!=length: raise ValueError
                fields=parse_qs(raw.decode('utf-8'),keep_blank_values=True,strict_parsing=True,max_num_fields=8)
                if set(fields)!={'id','timestamp','token','name','email','message'} or any(len(v)!=1 for v in fields.values()):
                    raise ValueError
                data={k:v[0] for k,v in fields.items()}
                ts=int(data['timestamp']); ident=data['id']
                if not re.fullmatch(r'[a-f0-9]{32}',ident) or not 0<=instant(clock()).timestamp()-ts<=3600:
                    raise ValueError
            except (ValueError,UnicodeError,TimeoutError):
                self.respond(400,'Invalid request'); return
            db=Orders(root,secret,config)
            try:
                slug=self.customer(db)
                if not hmac.compare_digest(data['token'],self.token(slug,ts,ident)):
                    self.respond(403,'Invalid token'); return
                at=instant(clock())
                with db.db:
                    db.db.execute('BEGIN IMMEDIATE')
                    cutoff=stamp(at-timedelta(minutes=10)); hour=stamp(at-timedelta(hours=1))
                    ip='ip:'+self.identity(); site='site:'+slug
                    if (db.db.execute('SELECT COUNT(*) FROM form_limits WHERE key=? AND at>=?',(ip,cutoff)).fetchone()[0]>=5 or
                        db.db.execute('SELECT COUNT(*) FROM form_limits WHERE key=? AND at>=?',(site,hour)).fetchone()[0]>=20):
                        self.respond(429,'Please try again later'); return
                    db.db.executemany('INSERT INTO form_limits VALUES(?,?)',[(ip,stamp(at)),(site,stamp(at))])
                    db.db.execute('DELETE FROM form_limits WHERE at<?',(stamp(at-timedelta(days=1)),))
                db.enquiry(ident,slug,at,name=data['name'],email=data['email'],message=data['message'])
                self.respond(202,'Your enquiry has been received. It is queued for forwarding to the business.')
            except (ValueError,TypeError): self.respond(400,'Invalid enquiry')
            finally: db.close()
    server=HTTPServer(('127.0.0.1',port),Handler)
    server.allowed_origin='http://127.0.0.1:'+str(server.server_port)
    return server
