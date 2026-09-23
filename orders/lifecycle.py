"""Local operational lifecycle and durable simulated effects. No network adapters."""
from calendar import monthrange
from datetime import timedelta
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import struct
import zipfile
import uuid

from sender.calendar import instant, stamp, CENTRAL
from .config import AMOUNT, https

PUBLIC={'index.html','privacy.html','style.css','house.svg','_headers'}


class DefiniteFailure(Exception):
    """Adapter proves the effect was not accepted."""


class FakeAdapter:
    offline=True

    def __init__(self,outcomes=()):
        self.outcomes=list(outcomes); self.accepted={}; self.calls=[]; self.lookup_available=True

    def perform(self,key,kind,payload,at):
        self.calls.append(key)
        if key in self.accepted:
            return self.accepted[key]
        outcome=self.outcomes.pop(0) if self.outcomes else 'done'
        if outcome=='failed':
            raise DefiniteFailure('Definite rejection')
        if outcome=='timeout':
            raise TimeoutError('Ambiguous result')
        result={'receipt':'fake-'+sha256(key.encode()).hexdigest()[:16],'completed_at':stamp(at)}
        if kind=='publish':
            result['url']='https://customers.example.invalid/'+payload['slug']+'/'
            result['https_verified']=True; result['status_code']=200
            result['artifact_sha256']=payload['artifact_sha256']
        self.accepted[key]=result
        if outcome=='timeout_accepted':
            raise TimeoutError('Response lost after acceptance')
        return result

    def lookup(self,key):
        if not self.lookup_available:
            raise TimeoutError('Lookup unavailable')
        return self.accepted.get(key)  # Contract: None proves absence, not an unavailable lookup.


class Lifecycle:
    def init_lifecycle(self):
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS fulfilment(order_id TEXT PRIMARY KEY REFERENCES orders(id),revision INTEGER DEFAULT 0,
            published_revision INTEGER,period_end TEXT,cancel_at TEXT,cancel_requested_at TEXT,refund_state TEXT,
            sender_prospect TEXT,sender_synced INTEGER DEFAULT 0);
          CREATE TABLE IF NOT EXISTS effects(key TEXT PRIMARY KEY,kind TEXT,order_id TEXT,payload TEXT,state TEXT,
            receipt TEXT,attempts INTEGER DEFAULT 0,created TEXT,updated TEXT,claim TEXT);
          CREATE TABLE IF NOT EXISTS changes(id TEXT PRIMARY KEY,order_id TEXT,at TEXT,due TEXT,patch TEXT,revision INTEGER,minutes INTEGER,state TEXT);
          CREATE TABLE IF NOT EXISTS exports(id TEXT PRIMARY KEY,order_id TEXT,at TEXT,path TEXT,digest TEXT,purpose TEXT);
          CREATE TABLE IF NOT EXISTS form_limits(key TEXT,at TEXT);
          CREATE INDEX IF NOT EXISTS form_limits_key_at ON form_limits(key,at);
        ''')

    def fulfilment(self,order_id):
        self.get(order_id)
        if not self.db.execute('SELECT 1 FROM fulfilment WHERE order_id=?',(order_id,)).fetchone():
            if self.db.in_transaction:
                self.db.execute('INSERT OR IGNORE INTO fulfilment(order_id) VALUES(?)',(order_id,))
            else:
                with self.db:
                    self.db.execute('INSERT OR IGNORE INTO fulfilment(order_id) VALUES(?)',(order_id,))
        return dict(self.db.execute('SELECT * FROM fulfilment WHERE order_id=?',(order_id,)).fetchone())

    def record(self,order_id):
        row=self.get(order_id)
        return json.loads(self.db.execute('SELECT record FROM previews WHERE slug=?',(row['slug'],)).fetchone()[0])

    def artifact_folder(self,order_id,revision=None):
        row=self.get(order_id)
        revision=self.fulfilment(order_id)['revision'] if revision is None else revision
        return self.root/'customers'/(row['slug']+(f'-r{revision}' if revision else ''))

    def _safe_file(self,path):
        path=Path(path)
        if path.is_symlink() or self.root not in path.resolve().parents:
            raise ValueError('Runtime file must stay inside private root')
        return path

    def _validate_receipt(self,kind,payload,receipt,at):
        if not isinstance(receipt,dict) or not receipt.get('receipt'):
            raise ValueError('Adapter returned no receipt')
        if kind=='publish':
            if (not https(receipt.get('url')) or receipt.get('status_code')!=200 or
                receipt.get('https_verified') is not True or receipt.get('artifact_sha256')!=payload['artifact_sha256'] or
                instant(receipt['completed_at'])>instant(at)):
                raise ValueError('Publication receipt is not valid for the requested artifact')

    def _effect(self,key,kind,order_id,payload,adapter,at):
        """Durable intent plus lookup; ambiguous effects are never blindly retried."""
        if not getattr(adapter,'offline',False):
            raise PermissionError('Only offline adapters are allowed in TASK-007')
        encoded=json.dumps(payload,sort_keys=True,separators=(',',':'))
        claim=uuid.uuid4().hex
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row=self.db.execute('SELECT * FROM effects WHERE key=?',(key,)).fetchone()
            if row and (row['kind'],row['order_id'],row['payload'])!=(kind,order_id,encoded):
                raise ValueError('Effect identity reused with changed payload')
            if row and row['state']=='done':
                return json.loads(row['receipt'])
            if not row:
                self.db.execute('INSERT INTO effects(key,kind,order_id,payload,state,created,updated) VALUES(?,?,?,?,?,?,?)',
                                (key,kind,order_id,encoded,'pending',stamp(at),stamp(at)))
        # Serialize the adapter with other workers after the durable intent exists.
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row=self.db.execute('SELECT * FROM effects WHERE key=?',(key,)).fetchone()
            if row['state']=='done':
                return json.loads(row['receipt'])
            if row['state']=='inflight' and instant(at)<instant(row['updated'])+timedelta(minutes=5):
                return None
            if row['state'] in {'unknown','inflight'}:
                try:
                    receipt=adapter.lookup(key)
                    if receipt is not None: self._validate_receipt(kind,payload,receipt,at)
                except Exception:
                    return None
                if receipt is not None:
                    self.db.execute("UPDATE effects SET state='done',receipt=?,updated=? WHERE key=?",(json.dumps(receipt),stamp(at),key))
                    return receipt
            if row['attempts']>=2:
                return None
            self.db.execute("UPDATE effects SET state='inflight',attempts=attempts+1,updated=?,claim=? WHERE key=?",(stamp(at),claim,key))
        # If this process disappears, the committed inflight row is reconciled above.
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            current=self.db.execute('SELECT * FROM effects WHERE key=?',(key,)).fetchone()
            if current['state']=='done': return json.loads(current['receipt'])
            if current['claim']!=claim: return None
            try:
                receipt=adapter.perform(key,kind,payload,at)
                self._validate_receipt(kind,payload,receipt,at)
                self.db.execute("UPDATE effects SET state='done',receipt=?,updated=? WHERE key=?",(json.dumps(receipt),stamp(at),key))
                return receipt
            except DefiniteFailure:
                self.db.execute("UPDATE effects SET state='failed',updated=? WHERE key=?",(stamp(at),key))
            except Exception:
                self.db.execute("UPDATE effects SET state='unknown',updated=? WHERE key=?",(stamp(at),key))
        return None

    def bind_sender(self,order_id,prospect_id,sender):
        """Both identifiers and email must agree before the durable paid bridge."""
        row=self.get(order_id); prospect=sender.get(prospect_id)
        if prospect['email']!=row['email'] or prospect['preview_slug']!=row['slug']:
            raise ValueError('Sender customer/preview mismatch')
        with self.db:
            f=self.fulfilment(order_id)
            if f['sender_prospect'] not in (None,prospect_id):
                raise ValueError('Order already bound to another prospect')
            self.db.execute('UPDATE fulfilment SET sender_prospect=? WHERE order_id=?',(prospect_id,order_id))
        # Store.paid is itself atomic/idempotent. Replay repairs a crash before the local marker.
        sender.paid(order_id,prospect_id,row['paid_at'])
        with self.db:
            self.db.execute('UPDATE fulfilment SET sender_synced=1 WHERE order_id=?',(order_id,))

    def apply_change(self,order_id,request_id,patch,at,*,verified=False,minutes=30,correction=False):
        from .flow import ID, business_deadline
        from generator.build import SERVICES
        if not verified:
            raise PermissionError('Verified customer request required')
        if not ID.fullmatch(request_id) or not isinstance(patch,dict) or not patch or type(minutes) is not int or not 0<minutes<=30:
            raise ValueError('Request must fit the small-update allowance')
        allowed={'phone','hours','services','headline','intro','prices','photo'}
        if set(patch)-allowed:
            raise ValueError('Unsupported update; manual scope review required')
        for key,value in patch.items():
            if key in {'hours','headline','intro','prices'}:
                if not isinstance(value,str) or not 1<=len(value.strip())<=500 or any(ord(c)<32 and c!='\n' for c in value):
                    raise ValueError('Invalid customer text')
            if key=='phone' and (not isinstance(value,str) or not re.fullmatch(r'\+1[2-9]\d{9}',value)):
                raise ValueError('US E.164 phone required')
            if key=='services' and (not isinstance(value,list) or not value or len(value)!=len(set(value)) or set(value)-SERVICES):
                raise ValueError('Unsupported service')
            if key=='photo':
                if not isinstance(value,dict) or set(value)!={'path','consent','alt'} or value['consent'] is not True or not isinstance(value['alt'],str) or not 1<=len(value['alt'])<=200:
                    raise ValueError('Photo requires explicit permission and alt text')
                image=self._safe_file(self.root/value['path']).read_bytes()
                if len(image)>5_000_000 or len(image)<33 or image[:8]!=b'\x89PNG\r\n\x1a\n' or image[12:16]!=b'IHDR':
                    raise ValueError('Only a local PNG is automated; other media requires review')
                width,height=struct.unpack('>II',image[16:24])
                if not (0<width<=4096 and 0<height<=4096):
                    raise ValueError('Photo dimensions exceed limits')
        encoded=json.dumps(patch,sort_keys=True)
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row=self.get(order_id); f=self.fulfilment(order_id)
            old=self.db.execute('SELECT * FROM changes WHERE id=?',(request_id,)).fetchone()
            if old:
                if (old['order_id'],old['patch'],old['minutes'])!=(order_id,encoded,minutes):
                    raise ValueError('Changed request payload')
                return dict(old)
            if row['status'] in {'cancelled','refunded'} or f['cancel_at'] and instant(at)>=instant(f['cancel_at']):
                raise ValueError('Paid service has ended')
            if correction and row['status']!='needs_corrections':
                raise ValueError('No unresolved launch corrections')
            if not correction and row['status'] not in {'live','cancel_pending'}:
                raise ValueError('Maintenance begins after launch')
            if not correction:
                # Subscription months follow the original payment day, clamped at month end.
                paid=instant(row['paid_at']).astimezone(CENTRAL); local=instant(at).astimezone(CENTRAL)
                day=min(paid.day,monthrange(local.year,local.month)[1])
                boundary=local.replace(day=day,hour=paid.hour,minute=paid.minute,second=paid.second,microsecond=paid.microsecond)
                if boundary>local:
                    year,month=(local.year-1,12) if local.month==1 else (local.year,local.month-1)
                    boundary=boundary.replace(year=year,month=month,day=min(paid.day,monthrange(year,month)[1]))
                count=self.db.execute("SELECT COUNT(*) FROM changes WHERE order_id=? AND at>=? AND state!='correction'",(order_id,stamp(boundary))).fetchone()[0]
                if count>=5:
                    raise ValueError('Five requests already used in this subscription month')
            record=self.record(order_id)
            for key,value in patch.items():
                if key=='photo':
                    image=self._safe_file(self.root/value['path']).read_bytes()
                    name=sha256(image).hexdigest()+'.png'; assets=self.root/'media'; assets.mkdir(exist_ok=True)
                    target=self._safe_file(assets/name)
                    if not target.exists(): target.write_bytes(image)
                    record['photo']=name; record['photo_alt']=value['alt']
                else:
                    record[key]=value
            revision=f['revision']+1
            self.db.execute('UPDATE previews SET record=? WHERE slug=?',(json.dumps(record),row['slug']))
            self.db.execute('UPDATE fulfilment SET revision=? WHERE order_id=?',(revision,order_id))
            if correction: self.db.execute("UPDATE orders SET status='ready' WHERE id=?",(order_id,))
            self.db.execute('INSERT INTO changes VALUES(?,?,?,?,?,?,?,?)',(request_id,order_id,stamp(at),business_deadline(at,2,self.config.get('us_federal_holidays',[])),encoded,revision,minutes,'correction' if correction else 'pending'))
        return dict(self.db.execute('SELECT * FROM changes WHERE id=?',(request_id,)).fetchone())

    def export_site(self,order_id,at,*,purpose='weekly'):
        if purpose not in {'weekly','cancellation','publish'}:
            raise ValueError('Unknown export purpose')
        folder=self.artifact_folder(order_id)
        record=self.record(order_id); allowed=PUBLIC|({record['photo']} if record.get('photo') else set())
        files={p.name:p for p in folder.iterdir()}
        if set(files)!=allowed or any(not p.is_file() or p.is_symlink() for p in files.values()):
            raise ValueError('Customer export contains missing or unapproved files')
        for p in files.values(): self._safe_file(p)
        digest=sha256(b''.join(name.encode()+b'\0'+files[name].read_bytes() for name in sorted(files))).hexdigest()
        ident=sha256((order_id+purpose+(stamp(at) if purpose=='weekly' else '')+digest).encode()).hexdigest()
        dest=self.root/'exports'; dest.mkdir(exist_ok=True); path=self._safe_file(dest/(ident+'.zip'))
        if not path.exists():
            temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
            with zipfile.ZipFile(temporary,'x',zipfile.ZIP_DEFLATED) as archive:
                for name in sorted(files): archive.writestr(name,files[name].read_bytes())
            temporary.replace(path)
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO exports VALUES(?,?,?,?,?,?)',(ident,order_id,stamp(at),str(path.relative_to(self.root)),digest,purpose))
        return {'path':str(path),'sha256':digest}

    def launch(self,order_id,at,host):
        row=self.get(order_id)
        if row['status'] not in {'prepared','live','cancel_pending'}:
            raise ValueError('Prepared customer artifact required')
        f=self.fulfilment(order_id)
        if f['cancel_at'] and instant(at)>=instant(f['cancel_at']):
            raise ValueError('Paid period has ended')
        self.promote(order_id)
        archive=self.export_site(order_id,at,purpose='publish')
        payload={'slug':row['slug'],'revision':f['revision'],'artifact_sha256':archive['sha256']}
        receipt=self._effect('publish:'+order_id+':'+str(f['revision']),'publish',order_id,payload,host,at)
        if receipt is None: return None
        if not https(receipt.get('url')) or receipt.get('status_code')!=200 or receipt.get('https_verified') is not True or receipt.get('artifact_sha256')!=archive['sha256']:
            raise ValueError('Host receipt does not prove this exact artifact is available')
        completed=instant(receipt['completed_at'])
        if completed>instant(at) or completed<max(instant(row['paid_at']),instant(row['confirmed_at'])):
            raise ValueError('Invalid host completion time')
        with self.db:
            self.db.execute("UPDATE orders SET status=?,live_at=COALESCE(live_at,?),live_url=? WHERE id=?",('cancel_pending' if f['cancel_at'] else 'live',stamp(completed),receipt['url'],order_id))
            self.db.execute('UPDATE fulfilment SET published_revision=? WHERE order_id=?',(f['revision'],order_id))
            self.db.execute("UPDATE changes SET state='completed' WHERE order_id=? AND revision<=? AND state='pending'",(order_id,f['revision']))
        self.project(); return receipt

    def send_welcome(self,order_id,at,mailer):
        row=self.get(order_id); self.project()
        draft=(self.root/'welcome'/(order_id+'.txt')).read_text(encoding='utf-8')
        body=draft.split('\n\n',1)[1].split('This is a private unsent draft.',1)[0].rstrip()
        body+='\n\nCancel anytime through your receipt email. Cancellation takes effect at the end of the paid month, with a ZIP export delivered.'
        payload={'to':row['email'],'subject':'Confirm your website details','body':body}
        return self._effect('welcome:'+order_id,'mail',order_id,payload,mailer,at)

    def set_period_end(self,order_id,period_end,*,verified=False):
        if not verified:
            raise PermissionError('Authenticated provider paid-period evidence required')
        row=self.get(order_id)
        if instant(period_end)<=instant(row['paid_at']): raise ValueError('Invalid paid period')
        with self.db:
            f=self.fulfilment(order_id)
            if f['cancel_at']: raise ValueError('Cancellation already fixes the paid period')
            self.db.execute('UPDATE fulfilment SET period_end=? WHERE order_id=?',(stamp(period_end),order_id))

    def cancel(self,order_id,at,provider,*,verified=False):
        if not verified: raise PermissionError('Verified customer cancellation required')
        row=self.get(order_id); f=self.fulfilment(order_id)
        if not f['period_end']: raise ValueError('Provider-confirmed paid-period end required')
        if row['status'] in {'refunded','cancelled'}: return row
        if f['cancel_at']: return row
        # Remember customer receipt, so retries cannot change the effect payload or clock.
        with self.db:
            self.db.execute('UPDATE fulfilment SET cancel_requested_at=COALESCE(cancel_requested_at,?) WHERE order_id=?',(stamp(at),order_id))
        receipt=self._effect('cancel:'+order_id,'cancel',order_id,{'order_id':order_id,'effective_at':f['period_end']},provider,at)
        if receipt is None: return None
        with self.db:
            self.db.execute('UPDATE fulfilment SET cancel_at=period_end WHERE order_id=?',(order_id,))
            self.db.execute("UPDATE orders SET status='cancel_pending' WHERE id=?",(order_id,))
        self.project(); return self.get(order_id)

    def finish_cancel(self,order_id,at,host,mailer):
        row=self.get(order_id); f=self.fulfilment(order_id)
        if row['status']=='cancelled': return row
        if not f['cancel_at'] or instant(at)<instant(f['cancel_at']):
            raise ValueError('Keep the site through the paid period')
        if not self.artifact_folder(order_id).exists(): self.promote(order_id,export_only=True)
        archive=self.export_site(order_id,f['cancel_at'],purpose='cancellation')
        payload={'to':row['email'],'subject':'Your website export','attachment':archive['path'],'sha256':archive['sha256']}
        if self._effect('export-mail:'+order_id,'mail',order_id,payload,mailer,at) is None: return None
        if self._effect('remove:'+order_id,'remove',order_id,{'slug':row['slug']},host,at) is None: return None
        with self.db:
            self.db.execute("UPDATE orders SET status='cancelled' WHERE id=?",(order_id,))
        self.project(); return self.get(order_id)

    def refund_overdue(self,at,provider):
        result=[]
        for row in self.refund_candidates(at):
            f=self.fulfilment(row['id'])
            if f['refund_state']=='done': continue
            payload={'order_id':row['id'],'amount_minor':AMOUNT,'currency':'USD','reason':'missed_five_business_day_launch'}
            receipt=self._effect('refund:'+row['id'],'refund',row['id'],payload,provider,at)
            if receipt is not None:
                with self.db:
                    self.db.execute("UPDATE fulfilment SET refund_state='done' WHERE order_id=?",(row['id'],))
                result.append(row['id'])
        return result

    def forward_enquiries(self,at,mailer):
        result=[]
        for enquiry in self.db.execute("SELECT * FROM enquiries WHERE status='pending'").fetchall():
            order=self.db.execute('SELECT * FROM orders WHERE slug=?',(enquiry['slug'],)).fetchone()
            payload={'to':order['email'],'reply_to':enquiry['email'],'subject':'Website enquiry',
                     'body':enquiry['name']+'\n'+enquiry['message']}
            if self._effect('enquiry:'+enquiry['id'],'mail',order['id'],payload,mailer,at) is not None:
                with self.db: self.db.execute("UPDATE enquiries SET status='sent' WHERE id=?",(enquiry['id'],))
                result.append(enquiry['id'])
        return result

    def weekly_exports(self,at):
        result=[]
        for row in self.db.execute("SELECT * FROM orders WHERE status IN ('live','cancel_pending')").fetchall():
            old=self.db.execute("SELECT MAX(at) FROM exports WHERE order_id=? AND purpose='weekly'",(row['id'],)).fetchone()[0]
            if not old or instant(at)>=instant(old)+timedelta(days=7):
                result.append(self.export_site(row['id'],at))
        # Exact known files only, resolved beneath runtime; never a recursive delete.
        for row in self.db.execute("SELECT * FROM exports WHERE purpose='weekly'").fetchall():
            if instant(at)>instant(row['at'])+timedelta(days=30):
                path=self._safe_file(self.root/row['path'])
                path.unlink(missing_ok=True)
                with self.db: self.db.execute('DELETE FROM exports WHERE id=?',(row['id'],))
        return result

    def tick(self,at,*,provider,host,mailer,sender=None):
        """One bounded invocation; deployment/scheduling remain owner-hosted dependencies."""
        if sender is not None:
            for row in self.db.execute('SELECT * FROM fulfilment WHERE sender_prospect IS NOT NULL AND sender_synced=0').fetchall():
                self.bind_sender(row['order_id'],row['sender_prospect'],sender)
        for effect in self.db.execute("SELECT DISTINCT order_id FROM effects WHERE kind='publish' AND state IN ('unknown','inflight')").fetchall():
            row=self.get(effect['order_id']); f=self.fulfilment(row['id'])
            if row['status'] in {'prepared','live','cancel_pending'} and not (f['cancel_at'] and instant(at)>=instant(f['cancel_at'])):
                self.launch(row['id'],at,host)
        refunded=self.refund_overdue(at,provider)
        forwarded=self.forward_enquiries(at,mailer)
        for row in self.db.execute("SELECT * FROM orders WHERE status='cancel_pending'").fetchall():
            f=self.fulfilment(row['id'])
            if f['cancel_at'] and instant(at)>=instant(f['cancel_at']): self.finish_cancel(row['id'],at,host,mailer)
        exports=self.weekly_exports(at)
        overdue=[r['id'] for r in self.db.execute("SELECT * FROM changes WHERE state='pending'") if instant(at)>instant(r['due'])]
        self.project()
        return {'refunded':refunded,'forwarded':forwarded,'exports':len(exports),'overdue_changes':overdue,'unresolved_effects':[dict(r) for r in self.db.execute("SELECT key,state,attempts FROM effects WHERE state!='done'")]}


    def monthly_report(self,order_id,month,at,mailer,*,visits=None):
        if not re.fullmatch(r'\d{4}-\d{2}',month): raise ValueError('Expected YYYY-MM')
        from datetime import date
        first=date.fromisoformat(month+'-01')
        if month>=instant(at).astimezone(CENTRAL).strftime('%Y-%m'):
            raise ValueError('Report a fully closed Central month only')
        if visits is not None and (type(visits) is not int or visits<0): raise ValueError('Invalid visit count')
        row=self.get(order_id)
        count=sum(instant(r['at']).astimezone(CENTRAL).strftime('%Y-%m')==month for r in self.db.execute('SELECT at FROM enquiries WHERE slug=?',(row['slug'],)))
        payload={'to':row['email'],'subject':'Your website report: '+month,
                 'body':'Visits: '+('n/a (analytics unavailable)' if visits is None else str(visits))+'\nForm submissions: '+str(count)}
        return self._effect('monthly:'+order_id+':'+month,'mail',order_id,payload,mailer,at)
