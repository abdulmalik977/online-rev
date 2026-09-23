"""Signed initial payments and confirmation -> private local customer artifacts.

This module cannot connect to a provider, send email, issue refunds or deploy.
Only an authenticated provider adapter may produce the normalized event schema.
"""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from html import escape
import hmac
import json
from pathlib import Path
import re
import sqlite3
import uuid
from string import Template
from urllib.parse import urlsplit

from sender.calendar import instant, stamp, next_business_day
from sender.rules import normalize
from .config import PLAN, AMOUNT, https
from .lifecycle import Lifecycle

ROOT=Path(__file__).resolve().parents[1]
ID=re.compile(r'[a-zA-Z0-9_-]{1,100}')
SLUG=re.compile(r'[a-z0-9][a-z0-9-]{1,100}')


def signature(raw,secret,timestamp):
    if not isinstance(secret,bytes) or len(secret)<32:
        raise ValueError('A private secret of at least 32 bytes is required')
    return hmac.new(secret,str(timestamp).encode('ascii')+b'.'+raw,sha256).hexdigest()


def business_deadline(start,days,holidays=()):
    result=instant(start)
    for _ in range(days):
        result=next_business_day(result,holidays)
    return stamp(result)


class Orders(Lifecycle):
    def __init__(self,root,secret,config):
        signature(b'',secret,0)
        self.root=Path(root).resolve(); self.root.mkdir(parents=True,exist_ok=True)
        self.secret=secret; self.config=config
        self.sender=None
        self.db=sqlite3.connect(self.root/'orders.sqlite',timeout=10)
        self.db.row_factory=sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS previews(slug TEXT PRIMARY KEY,email TEXT NOT NULL,expires TEXT NOT NULL,record TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY,slug TEXT NOT NULL UNIQUE REFERENCES previews(slug),email TEXT NOT NULL,
            paid_at TEXT NOT NULL,confirmed_at TEXT,confirmation TEXT,status TEXT NOT NULL,launch_due TEXT,refund_due TEXT,live_at TEXT,live_url TEXT);
          CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,digest TEXT NOT NULL,order_id TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,at TEXT NOT NULL,action TEXT NOT NULL,order_id TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS enquiries(id TEXT PRIMARY KEY,slug TEXT NOT NULL,at TEXT NOT NULL,name TEXT NOT NULL,email TEXT NOT NULL,message TEXT NOT NULL,status TEXT NOT NULL);
        ''')
        self.init_lifecycle()

    def close(self):
        self.db.close()

    def register_preview(self,bundle,slug,email,at):
        """Import trusted generator data privately; no arbitrary HTML or paths copied."""
        if not SLUG.fullmatch(slug):
            raise ValueError('Invalid preview slug')
        bundle=Path(bundle).resolve()
        report=json.loads((bundle/'build-report.json').read_text(encoding='utf-8'))
        expires=report['expires']+'T00:00:00+00:00'
        if report['expired'] or instant(at)>=instant(expires):
            raise ValueError('Preview has expired; do not reset its age')
        records=json.loads((bundle/'records.json').read_text(encoding='utf-8'))
        rows=[r for r in records if r['slug']==slug]
        page=bundle/'previews'/slug/'index.html'
        if len(rows)!=1 or not page.is_file() or page.is_symlink() or bundle not in page.resolve().parents:
            raise ValueError('Generated preview missing or unsafe')
        record=rows[0]
        if record['city']!='Houston' or record['state']!='TX' or record['style'] not in (0,1,2):
            raise ValueError('Unsupported preview')
        with self.db:
            self.db.execute('INSERT INTO previews VALUES(?,?,?,?)',(slug,normalize(email),expires,json.dumps(record)))

    def accept(self,raw,timestamp,mac,at):
        """Verify before parsing or writing. Five-minute skew; signed retries must be fresh."""
        if not isinstance(raw,bytes) or len(raw)>16384:
            raise ValueError('Invalid event size')
        if type(timestamp) is not int or abs(instant(at).timestamp()-timestamp)>300:
            raise ValueError('Webhook timestamp is outside five-minute tolerance')
        if not isinstance(mac,str) or not hmac.compare_digest(signature(raw,self.secret,timestamp),mac):
            raise ValueError('Invalid signature')
        event=json.loads(raw)
        required={'event_id','type','order_id','email','preview_slug','plan','amount_minor','currency','paid_at'}
        if not isinstance(event,dict) or set(event)!=required:
            raise ValueError('Invalid normalized event schema')
        if event['type']!='order.paid' or event['plan']!=PLAN or type(event['amount_minor']) is not int or event['amount_minor']!=AMOUNT or event['currency']!='USD':
            raise ValueError('Not an initial USD 119 payment for this plan')
        if any(not isinstance(event[k],str) or not ID.fullmatch(event[k]) for k in ('event_id','order_id')):
            raise ValueError('Invalid event/order identity')
        if not isinstance(event['preview_slug'],str) or not SLUG.fullmatch(event['preview_slug']):
            raise ValueError('Invalid preview identity')
        paid=instant(event['paid_at']); email=normalize(event['email']); digest=sha256(raw).hexdigest()
        if paid>instant(at):
            raise ValueError('Payment cannot be in the future')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            seen=self.db.execute('SELECT * FROM events WHERE id=?',(event['event_id'],)).fetchone()
            if seen:
                if seen['digest']!=digest:
                    raise ValueError('Event ID reused with different content')
                self.db.commit(); self.sync_paid(seen['order_id']); self.project(); return self.get(seen['order_id'])
            preview=self.db.execute('SELECT * FROM previews WHERE slug=?',(event['preview_slug'],)).fetchone()
            if not preview or preview['email']!=email or instant(preview['expires'])<=paid:
                raise ValueError('Payment has no matching unexpired registered preview/customer')
            existing=self.db.execute('SELECT * FROM orders WHERE id=?',(event['order_id'],)).fetchone()
            if existing:
                if (existing['slug'],existing['email'],existing['paid_at'])!=(preview['slug'],email,stamp(paid)):
                    raise ValueError('Order ID conflict')
            else:
                self.db.execute('INSERT INTO orders(id,slug,email,paid_at,status) VALUES(?,?,?,?,?)',
                                (event['order_id'],preview['slug'],email,stamp(paid),'awaiting_confirmation'))
                self.db.execute('INSERT INTO audit(at,action,order_id) VALUES(?,?,?)',(stamp(at),'payment_recorded',event['order_id']))
            self.db.execute('INSERT INTO events VALUES(?,?,?)',(event['event_id'],digest,event['order_id']))
            self.db.commit()
        except BaseException:
            self.db.rollback(); raise
        self.sync_paid(event['order_id'])
        self.project()
        return self.get(event['order_id'])

    def sync_paid(self,order_id):
        if self.sender is not None:
            row=self.get(order_id); prospect=self.sender.by_email(row['email'])
            if prospect is not None:
                self.bind_sender(order_id,prospect['id'],self.sender)

    def wire_sender(self,engine):
        self.sender=engine.store
        def guard(prospect,at):
            # Read the authoritative paid ledger during both sender transactions.
            # This closes the crash window between the two SQLite databases.
            for row in self.db.execute('SELECT * FROM orders WHERE email=?',(prospect['email'],)).fetchall():
                if row['slug']!=prospect['preview_slug']:
                    raise ValueError('Paid order preview mismatch; refuse sending')
                engine.store.paid(row['id'],prospect['id'],row['paid_at'])
        engine.order_guard=guard
        for row in self.db.execute('SELECT id FROM orders').fetchall():
            self.sync_paid(row['id'])

    def get(self,order_id):
        row=self.db.execute('SELECT * FROM orders WHERE id=?',(order_id,)).fetchone()
        if not row:
            raise ValueError('Unknown order')
        return dict(row)

    def confirm(self,order_id,email,at,*,domain,corrections,media_consent,verified=False):
        """Trusted inbox/operator boundary, never a public unauthenticated endpoint."""
        if not verified:
            raise PermissionError('Authenticated customer confirmation required')
        if domain!='subdomain' and not re.fullmatch(r'(?=.{3,253}$)(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,63}',domain):
            raise ValueError('Choose subdomain or a domain name')
        if not isinstance(corrections,str) or len(corrections)>3000 or type(media_consent) is not bool:
            raise ValueError('Explicit corrections and media consent required')
        value=json.dumps({'domain':domain,'corrections':corrections.strip(),'media_consent':media_consent},sort_keys=True)
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row=self.get(order_id)
            if normalize(email)!=row['email']:
                raise ValueError('Confirmation customer mismatch')
            if row['confirmed_at']:
                if row['confirmation']!=value:
                    raise ValueError('Confirmation already recorded; process changes separately')
                return row
            start=max(instant(row['paid_at']),instant(at))
            holidays=self.config.get('us_federal_holidays',[])
            # Correction text is never silently treated as implemented.
            status='needs_corrections' if corrections.strip() else 'ready'
            self.db.execute('UPDATE orders SET confirmed_at=?,confirmation=?,status=?,launch_due=?,refund_due=? WHERE id=?',
                            (stamp(at),value,status,business_deadline(start,2,holidays),business_deadline(start,5,holidays),order_id))
            self.db.execute('INSERT INTO audit(at,action,order_id) VALUES(?,?,?)',(stamp(at),'customer_confirmed',order_id))
        self.project(); return self.get(order_id)

    def promote(self,order_id,*,export_only=False):
        row=self.get(order_id)
        if row['status'] not in {'ready','prepared','live','cancel_pending'}:
            raise ValueError('Payment, confirmation and corrections must be resolved first')
        resolved=bool(self.db.execute("SELECT 1 FROM changes WHERE order_id=? AND state='correction'",(order_id,)).fetchone())
        if not export_only and (not row['confirmed_at'] or (json.loads(row['confirmation'])['corrections'] and not resolved)):
            raise ValueError('Customer confirmation and implemented corrections required')
        if export_only and row['status']!='cancel_pending':
            raise ValueError('Export-only preparation is for cancellation only')
        record=json.loads(self.db.execute('SELECT record FROM previews WHERE slug=?',(row['slug'],)).fetchone()[0])
        folder=self.artifact_folder(order_id)
        # Deterministic files allow recovery after a crash between file writes and DB update.
        folder.mkdir(parents=True,exist_ok=True)
        if folder.is_symlink() or self.root not in folder.resolve().parents:
            raise ValueError('Unsafe output directory')
        e=escape
        endpoint=self.config.get('contact_form_base_url','')
        form_origin="'none'"; form='<p>For enquiries, please use the phone link above. The online form is not available yet.</p>'
        if https(endpoint) and self.config.get('form_delivery_verified') is True:
            action=endpoint.rstrip('/')+'/'+row['slug']
            p=urlsplit(endpoint); form_origin=p.scheme+'://'+p.netloc
            form=f'<p><a class="button" href="{e(action)}">Send an enquiry</a></p><p>Open our contact page to send your details securely to this business.</p>'
        page=Template((ROOT/'orders/customer.html').read_text(encoding='utf-8')).substitute(
            name=e(record['business']),trade='Plumbing &amp; HVAC' if record['category']=='plumbing_hvac' else 'Plumbing',
            style=record['style'],form_origin=e(form_origin,quote=True),form=form,
            phone=f'<a class="button" href="tel:{e(record["phone"])}">Call {e(record["phone"])}</a>' if record['phone'] else '',
            services=''.join(f'<li><h3>{e(s)}</h3></li>' for s in record['services']),
            hours='<p>'+e(record['hours'])+'</p>' if record.get('hours') else '',
            headline=e(record.get('headline','A home that keeps flowing.')),intro=e(record.get('intro',"Explore "+record['business']+"'s services for Houston homes.")),
            prices='<p>'+e(record['prices'])+'</p>' if record.get('prices') else '',
            artwork=e(record.get('photo','house.svg')),photo_alt=e(record.get('photo_alt','Original illustration of a house and water pipes')))
        privacy=f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Privacy</title><link rel="stylesheet" href="style.css"><main class="wrap section"><h1>Privacy</h1><p>Enquiries are forwarded to {e(record["business"])} using the details you provide. Do not submit sensitive information. This site sets no cookies.</p><a href="./">Back to the website</a></main></html>'
        files={'index.html':page.encode(),'privacy.html':privacy.encode(),
               'style.css':(ROOT/'generator/style.css').read_bytes(),
               'house.svg':(ROOT/'generator/house.svg').read_bytes(),
               '_headers':b'/*\n  Cache-Control: no-cache\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: no-referrer\n'}
        if record.get('photo'):
            files[record['photo']]=self._safe_file(self.root/'media'/record['photo']).read_bytes()
        for name,data in files.items():
            target=folder/name
            if target.exists() and (target.is_symlink() or target.read_bytes()!=data):
                raise ValueError('Existing customer artifact differs; do not overwrite it')
            if not target.exists():
                with target.open('xb') as handle: handle.write(data)
        with self.db:
            self.db.execute("UPDATE orders SET status=CASE WHEN status IN ('live','cancel_pending') THEN status ELSE 'prepared' END WHERE id=?",(order_id,))
        self.project()
        return folder

    def refund_candidates(self,at):
        return [dict(r) for r in self.db.execute('SELECT * FROM orders WHERE refund_due IS NOT NULL')
                if instant(at)>=instant(r['refund_due']) and (not r['live_at'] or instant(r['live_at'])>instant(r['refund_due']))]

    def project(self):
        """Recoverable private projection; database is the authority."""
        drafts=self.root/'welcome'; drafts.mkdir(exist_ok=True)
        lines=['# Orders (private)','','Local preparation is not hosted launch. No email or refund is sent by this module.','']
        for row in self.db.execute('SELECT * FROM orders ORDER BY paid_at,id'):
            lines.append(f'- {row["id"]} | {row["slug"]} | {row["status"]} | launch {row["launch_due"] or "awaiting confirmation"} | refund eligibility {row["refund_due"] or "awaiting confirmation"}')
            draft=(f'To: {row["email"]}\nSubject: Confirm your website details\n\n'
                   'Thanks for your order. Please reply with:\n1. Your domain, or use our subdomain.\n'
                   '2. Any corrections to the preview (or say no corrections).\n'
                   '3. Confirmation that you own or may use any photos/logo/testimonials you supply.\n\n'
                   'Launch: two business days (Mon-Fri, US Central) from the later of payment and this confirmation. '
                   'If not live on our subdomain within five business days of that start, the first month is refunded automatically.\n\n'
                   'DNS: we will send the exact host-provided CNAME or A records after provisioning. '
                   'Open the DNS settings for your domain, add only those records, and preserve existing MX/email records. '
                   'Until DNS is connected, your site will run on our subdomain. No DNS values are assigned yet.\n\n'
                   'This is a private unsent draft. Cancellation and provider receipt links are not configured.\n')
            target=drafts/(row['id']+'.txt'); temporary=target.with_name(target.name+'.'+uuid.uuid4().hex+'.tmp')
            temporary.write_text(draft,encoding='utf-8'); temporary.replace(target)
        lines+=['','## Effects requiring reconciliation or retry']
        for effect in self.db.execute("SELECT key,state,attempts FROM effects WHERE state!='done'"):
            lines.append(f"- {effect['key']} | {effect['state']} | attempts {effect['attempts']}")
        target=self.root/'orders.md'; temporary=target.with_name(target.name+'.'+uuid.uuid4().hex+'.tmp')
        temporary.write_text('\n'.join(lines)+'\n',encoding='utf-8'); temporary.replace(target)

    def enquiry(self,ident,slug,at,*,name,email,message):
        """Private form outbox only. Hosting/rate limiting and delivery remain launch gates."""
        if not ID.fullmatch(ident) or not SLUG.fullmatch(slug):
            raise ValueError('Invalid form identity')
        if not isinstance(name,str) or not 1<=len(name.strip())<=120 or not isinstance(message,str) or not 1<=len(message.strip())<=3000:
            raise ValueError('Invalid enquiry')
        if any(c in name or c in email for c in ('\r','\n')):
            raise ValueError('Header injection refused')
        email=normalize(email)
        if not self.db.execute("SELECT 1 FROM orders WHERE slug=? AND status IN ('prepared','live','cancel_pending')",(slug,)).fetchone():
            raise ValueError('Customer site not prepared')
        with self.db:
            old=self.db.execute('SELECT * FROM enquiries WHERE id=?',(ident,)).fetchone()
            if old and (old['slug'],old['name'],old['email'],old['message'])!=(slug,name.strip(),email,message.strip()):
                raise ValueError('Enquiry id conflict')
            self.db.execute('INSERT OR IGNORE INTO enquiries VALUES(?,?,?,?,?,?,?)',(ident,slug,stamp(at),name.strip(),email,message.strip(),'pending'))
        return {'status':'pending','delivered':False}
