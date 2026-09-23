"""Transactional application core. Transport injection is restricted to offline fakes."""
from dataclasses import asdict
from datetime import timedelta
from hashlib import sha256
import hmac
import json
import uuid

from .calendar import instant, stamp, local_day, expiry, due, next_slot, service_due, cap, CENTRAL
from .rules import parse, decide, normalize, SHARED, ROLES, TERMINAL, matches
from .templates import stable_index, render, variables, fill, SIGNATURE


class DefiniteFailure(Exception):
    """Transport establishes that SMTP did not accept this message."""


class Engine:
    def __init__(self, store, config, secret):
        from .gate import validate
        validate(config)
        if len(secret)<32:
            raise ValueError('At least 32 secret bytes required for opt-out tokens')
        self.store,self.config,self.secret=store,config,secret
        self.holidays=config.get('us_federal_holidays',[])
        self.shared=set(config.get('shared_mail_domains',sorted(SHARED)))
        with store.transaction() as conn:
            for mailbox in config['mailboxes']:
                conn.execute('INSERT OR IGNORE INTO mailboxes(id) VALUES(?)',(mailbox,))
            # Upgrade pending A6 queue clocks using their original receipt time.
            for row in conn.execute('SELECT id,created FROM queue WHERE resolved=0').fetchall():
                conn.execute('UPDATE queue SET due=? WHERE id=?',
                             (store.owner_due(row['created'],self.holidays),row['id']))

    def token(self, ident):
        return hmac.new(self.secret,ident.encode(),sha256).hexdigest()

    def optout(self, token, at):
        with self.store.transaction() as conn:
            for row in conn.execute('SELECT id FROM prospects'):
                if hmac.compare_digest(self.token(row['id']),token):
                    p=self.store.get(row['id'])
                    self.store.suppress(p['email'],'unsubscribe',at,'optout:'+token,self.shared,p)
                    if p['state'] not in TERMINAL:
                        p['state']='suppressed'
                    self.store.save(p)
                    return True
        return False

    def mailbox(self,p):
        if p.get('mailbox'):
            return p['mailbox']
        active=[m for m in self.config['mailboxes'] if m in self.config.get('auth_passed',[])]
        if not active:
            raise ValueError('No authenticated mailbox')
        return active[stable_index(p['id'],len(active))]

    def _message(self,p,number=None,reply=None,faq=(),message_id=None):
        return render(self.config,p,self.token(p['id']),message_id or '<'+uuid.uuid4().hex+'@'+self.config['sending_domain']+'>',number,reply,faq)

    def _pause(self, mailbox, at, hours):
        row=self.store.conn.execute('SELECT * FROM mailboxes WHERE id=?',(mailbox,)).fetchone()
        if not row:
            return
        recent=[t for t in json.loads(row['pauses']) if instant(t)>=instant(at)-timedelta(days=7)]
        if row['pause_until'] and instant(row['pause_until'])>instant(at):
            until=max(instant(row['pause_until']),instant(at)+timedelta(hours=hours))
        else:
            recent.append(stamp(at)); until=instant(at)+timedelta(hours=hours)
        self.store.conn.execute('UPDATE mailboxes SET pause_until=?,pauses=?,disabled=? WHERE id=?',
                                (stamp(until),json.dumps(recent),int(row['disabled'] or len(recent)>=2),mailbox))

    def complaint(self,ident,p,at,reply_based=False):
        mailbox=p.get('mailbox')
        if not mailbox:
            return
        conn=self.store.conn
        inserted=conn.execute('INSERT OR IGNORE INTO events(id,mailbox,kind,at,recipient) VALUES(?,?,?,?,?)',
                              (ident,mailbox,'complaint',stamp(at),p['email'])).rowcount
        if not inserted:
            return
        self.store.suppress(p['email'],'complaint',at,ident,self.shared,p)
        day=local_day(at)
        in_window=lambda value: 0 <= (day-local_day(value)).days < 7
        complaints=sum(in_window(r['at']) for r in conn.execute("SELECT at FROM events WHERE mailbox=? AND kind='complaint'",(mailbox,)))
        accepted=sum(in_window(r['accepted_at']) for r in conn.execute("SELECT accepted_at FROM sends WHERE mailbox=? AND status='sent'",(mailbox,)))
        if reply_based:
            self._pause(mailbox,at,24)
        if complaints>=1 and accepted>=50:
            self._pause(mailbox,at,48)
        if complaints>=2:
            conn.execute('UPDATE mailboxes SET disabled=1 WHERE id=?',(mailbox,))

    def feedback(self,event_id,prospect_id,at):
        if not self.config.get('complaint_feed',False):
            raise ValueError('No complaint feed configured')
        with self.store.transaction():
            self.complaint(event_id,self.store.get(prospect_id),at)

    def receive(self,raw,at,*,mailbox_id=None,provider_uid=None):
        receiver=None
        if mailbox_id is not None:
            receiver=normalize(mailbox_id if '@' in mailbox_id else mailbox_id+'@'+self.config['sending_domain'])
            configured={m+'@'+self.config['sending_domain'] for m in self.config['mailboxes']}
            if receiver not in configured:
                raise ValueError('Receiving mailbox is not configured')
        event=parse(raw,mailbox_id=receiver,provider_uid=provider_uid)
        with self.store.transaction() as conn:
            if conn.execute('SELECT 1 FROM inbound WHERE id=?',(event['id'],)).fetchone():
                return {'kind':'duplicate'}
            # DSNs are correlated before checking the outer sender (A6).
            if event['dsn']:
                outcomes=[]
                for address,status in event['recipients']:
                    p=self.store.by_email(address)
                    send=conn.execute("SELECT * FROM sends WHERE prospect_id=? ORDER BY id DESC LIMIT 1",(p['id'],)).fetchone() if p else None
                    if not send:
                        continue
                    reference=next((r for r in event['references'] if conn.execute('SELECT 1 FROM sends WHERE message_id=?',(r,)).fetchone()),None)
                    if reference:
                        send=conn.execute('SELECT * FROM sends WHERE message_id=?',(reference,)).fetchone()
                        if send['prospect_id']!=p['id']:
                            continue
                    conn.execute('INSERT OR IGNORE INTO events VALUES(?,?,?,?,?,?)',
                                 (event['id']+':'+address,send['mailbox'],'hard' if status.startswith('5') else 'soft',stamp(at),address,send['id'],))
                    if status.startswith('5'):
                        self.store.suppress(address,'bounce_hard',at,event['id'],self.shared)
                    else:
                        recent=conn.execute("SELECT COUNT(*) FROM events WHERE kind='soft' AND recipient=? AND at>=?",(address,stamp(instant(at)-timedelta(days=30)))).fetchone()[0]
                        if recent>=3:
                            self.store.suppress(address,'bounce_soft_x3',at,event['id'],self.shared)
                    outcomes.append(address)
                conn.execute('INSERT INTO inbound VALUES(?,?,?,?,?)',(event['id'],None,stamp(at),'dsn',json.dumps(outcomes)))
                return {'kind':'dsn','recipients':outcomes}
            p=self.store.by_email(event['sender'])
            if not p:
                for ref in event['references']:
                    row=conn.execute('SELECT prospect_id FROM sends WHERE message_id=?',(ref,)).fetchone()
                    if row:
                        p=self.store.get(row[0]); break
            internal=event['sender'].rsplit('@',1)[1] in self.config.get('internal_domains',[])
            if internal or not p:
                kind='internal' if internal else 'unknown_sender'
                conn.execute('INSERT INTO inbound VALUES(?,?,?,?,?)',(event['id'],None,stamp(at),kind,'{}'))
                if not internal:
                    self.store.enqueue(None,event['id'],kind,at,'Identify sender; no automated response.',self.holidays)
                return {'kind':kind}
            signature=fill(SIGNATURE,variables(self.config,p,self.token(p['id'])))
            event=parse(raw,signature,mailbox_id=receiver,provider_uid=provider_uid)
            count=conn.execute("SELECT COUNT(*) FROM sends WHERE prospect_id=? AND kind='service' AND template NOT IN ('ACK_UNSUB','ACK_REFUND','OWNER') AND status!='failed'",(p['id'],)).fetchone()[0]
            decision=decide(event,p['state'],count)
            p['state']=decision.state
            if decision.state=='not_now':
                p['not_now_until']=stamp(instant(at)+timedelta(days=60))
            for reason in decision.suppression:
                self.store.suppress(p['email'],reason,at,event['id'],self.shared,p)
            if not event['auto'] and matches(event['body'],['spam']) and matches(event['body'],['report','reported','complaint']):
                self.complaint(event['id'],p,at,reply_based=True)
            self.store.save(p)
            for kind in decision.queue:
                draft='Owner decision required; no reply authorized.' if kind=='legal' else 'Review the inbound request and prepare an answer.'
                self.store.enqueue(p['id'],event['id'],kind,at,draft,self.holidays)
            if decision.reply:
                p['mailbox']=self.mailbox(p); self.store.save(p)
                message=self._message(p,reply=decision.reply,faq=decision.faq)
                conn.execute('INSERT INTO sends(prospect_id,email_no,kind,mailbox,message_id,status,created,updated,attempt,template,body,not_before) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                              (p['id'],'reply:'+event['id'],'service',p['mailbox'],str(message['Message-ID']),'pending',stamp(at),stamp(at),0,decision.reply,message.as_string(),stamp(service_due(at,self.holidays))))
            result=asdict(decision)
            conn.execute('INSERT INTO inbound VALUES(?,?,?,?,?)',(event['id'],p['id'],stamp(at),decision.kind,json.dumps(result)))
            return result

    def _eligible(self,p,number,at):
        if p.get('region') not in self.config.get('target_regions',[]):
            return 'region'
        if p['email'].split('@')[0] in ROLES:
            return 'role_address'
        if p['state'] not in {'queued','active'} or self.store.suppressed(p['email']):
            return 'state_or_suppression'
        if self.store.conn.execute('SELECT 1 FROM orders WHERE prospect_id=?',(p['id'],)).fetchone():
            return 'paid'
        if instant(at)>=instant(p['expiry_utc'])-timedelta(hours=24):
            p['state']='expired'; self.store.save(p); return 'expired'
        if p.get('not_now_until') and instant(at)<instant(p['not_now_until']):
            return 'not_now'
        if not p.get('first_send_at') and instant(at)>instant(p['generated_at'])+timedelta(hours=24):
            return 'regenerate_batch'
        planned=due(p,number,self.holidays)
        if planned is None or instant(at)<planned or next_slot(at,self.holidays)!=instant(at):
            return 'outside_slot'
        for previous in range(1,number):
            if not self.store.conn.execute("SELECT 1 FROM sends WHERE prospect_id=? AND email_no=? AND status='sent'",(p['id'],str(previous))).fetchone():
                return 'previous_unsent'
        return None

    def dispatch(self,prospect_id,number,at,transport,service_job=None):
        if not getattr(transport,'offline',False):
            raise PermissionError('TASK-009 has no live sending capability')
        from .gate import validate
        conn=self.store.conn
        with self.store.transaction():
            try:
                validate(self.config)
            except (ValueError,TypeError,KeyError,AttributeError):
                return 'invalid_config'
            p=self.store.get(prospect_id)
            job=service_job or str(number)
            row=conn.execute('SELECT * FROM sends WHERE prospect_id=? AND email_no=?',(prospect_id,job)).fetchone()
            if row and row['status'] in {'sending','sent','unknown'}:
                return row['status']
            if row and row['attempt']>=2:
                return 'retry_exhausted'
            if conn.execute("SELECT 1 FROM sends WHERE prospect_id=? AND status IN ('unknown','sending')",(prospect_id,)).fetchone():
                return 'held'
            if service_job:
                if not row or row['kind']!='service':
                    raise ValueError('Unknown service job')
                if instant(at)<instant(row['not_before']):
                    return 'reply_not_due'
            else:
                reason=self._eligible(p,number,at)
                if reason:
                    return reason
            mailbox=self.mailbox(p)
            m=conn.execute('SELECT * FROM mailboxes WHERE id=?',(mailbox,)).fetchone()
            if m['disabled'] or mailbox not in self.config.get('auth_passed',[]):
                return 'mailbox_disabled'
            if m['pause_until'] and instant(at)<instant(m['pause_until']):
                return 'mailbox_paused'
            day=local_day(at)
            reserved=[r for r in conn.execute("SELECT * FROM sends WHERE status IN ('sending','sent','unknown')") if local_day(r['created'])==day]
            if sum(r['mailbox']==mailbox for r in reserved)>=cap(m['first_send'],at):
                if service_job:
                    conn.execute('UPDATE sends SET not_before=? WHERE id=?',(stamp(service_due(at,self.holidays,True)),row['id']))
                return 'daily_cap'
            if not service_job:
                if conn.execute("SELECT 1 FROM sends WHERE kind='service' AND status='pending' AND mailbox=? AND not_before<=?",(mailbox,stamp(at))).fetchone():
                    return 'service_priority'
                domain=p['email'].rsplit('@',1)[1]
                count=sum(r['kind']=='outreach' and self.store.get(r['prospect_id'])['email'].rsplit('@',1)[1]==domain for r in reserved)
                if domain not in self.shared and count>=5:
                    return 'domain_cap'
            p['mailbox']=mailbox; p.setdefault('subject_variant',stable_index(p['id'],3))
            message_id=row['message_id'] if row else '<'+uuid.uuid4().hex+'@'+self.config['sending_domain']+'>'
            if number==1 and not service_job:
                p['thread_message_id']=message_id
            if p['state']=='queued':
                p['state']='active'
            self.store.save(p)
            body=row['body'] if service_job else self._message(p,number=number,message_id=message_id).as_string()
            if row:
                conn.execute("UPDATE sends SET status='sending',created=?,updated=?,attempt=attempt+1,body=? WHERE id=?",(stamp(at),stamp(at),body,row['id']))
                send_id=row['id']
            else:
                send_id=conn.execute('INSERT INTO sends(prospect_id,email_no,kind,mailbox,message_id,status,created,updated,attempt,body) VALUES(?,?,?,?,?,?,?,?,?,?)',
                                     (p['id'],job,'outreach',mailbox,message_id,'sending',stamp(at),stamp(at),1,body)).lastrowid
            conn.execute('UPDATE mailboxes SET first_send=COALESCE(first_send,?) WHERE id=?',(stamp(at),mailbox))
        # The committed intent survives process loss. A new write lock serializes
        # inbound mutations with this final send-time check and fake transport.
        with self.store.transaction():
            try:
                validate(self.config)
            except (ValueError,TypeError,KeyError,AttributeError):
                conn.execute("UPDATE sends SET status='failed',updated=? WHERE id=?",(stamp(at),send_id))
                return 'invalid_config'
            p=self.store.get(prospect_id)
            if not service_job and (p['state'] not in {'queued','active'} or self.store.suppressed(p['email']) or conn.execute('SELECT 1 FROM orders WHERE prospect_id=?',(prospect_id,)).fetchone()):
                conn.execute("UPDATE sends SET status='failed',updated=? WHERE id=?",(stamp(at),send_id))
                return 'cancelled_before_send'
            try:
                transport.send(message_id,body)
                status='sent'
            except DefiniteFailure:
                status='failed'
            except Exception:
                status='unknown'
            conn.execute('UPDATE sends SET status=?,updated=?,accepted_at=? WHERE id=?',(status,stamp(at),stamp(at) if status=='sent' else None,send_id))
            if status=='unknown':
                self._unknown_queue(conn.execute('SELECT * FROM sends WHERE id=?',(send_id,)).fetchone(),at)
            if status=='sent' and number==1 and not service_job:
                p['first_send_at']=stamp(at); self.store.save(p)
            return status

    def _unknown_queue(self,row,at):
        draft=('Delivery outcome unknown. Do not resend automatically. Reconcile '+row['message_id']+
               ' as sent or failed using explicit owner approval and an evidence note. Send row: '+str(row['id']))
        self.store.enqueue(row['prospect_id'],row['message_id'],'unknown_send',at,draft,self.holidays)
        # A permitted retry can itself become unknown with the same Message-ID.
        # Reopen its stable queue item, while prior owner decisions remain audited.
        self.store.conn.execute("UPDATE queue SET resolved=0,created=?,due=?,draft=? WHERE source=? AND class='unknown_send' AND resolved=1",
                                (stamp(at),self.store.owner_due(at,self.holidays),draft,row['message_id']))

    def _settle_unknown(self,row,status,at):
        conn=self.store.conn
        conn.execute('UPDATE sends SET status=?,updated=?,accepted_at=? WHERE id=?',
                     (status,stamp(at),row['created'] if status=='sent' else None,row['id']))
        conn.execute("UPDATE queue SET resolved=1 WHERE source=? AND class='unknown_send'",(row['message_id'],))
        if status=='sent' and row['email_no']=='1':
            p=self.store.get(row['prospect_id']); p.setdefault('first_send_at',row['created']); self.store.save(p)

    def reconcile(self,at,imap):
        if not getattr(imap,'offline',False):
            raise PermissionError('Only fake IMAP permitted in this task')
        outcomes=[]
        with self.store.transaction() as conn:
            conn.execute("UPDATE sends SET status='unknown' WHERE status='sending' AND updated<=?",(stamp(instant(at)-timedelta(minutes=5)),))
            for row in conn.execute("SELECT * FROM sends WHERE status='unknown'").fetchall():
                self._unknown_queue(row,at)
                try:
                    found=imap.contains(row['mailbox'],row['message_id'])
                except Exception:
                    found=False  # Missing/unavailable Sent never proves non-acceptance.
                if found:
                    self._settle_unknown(row,'sent',at)
                outcomes.append((row['message_id'],'sent' if found else 'unknown'))
        return outcomes

    def resolve_unknown_send(self,queue_id,at,outcome,*,approved=False,note=''):
        if not approved:
            raise PermissionError('Explicit owner reconciliation required')
        if outcome not in {'sent','failed'} or not isinstance(note,str) or not note.strip():
            raise ValueError('A sent/failed decision and evidence note are required')
        with self.store.transaction() as conn:
            queues=conn.execute("SELECT * FROM queue WHERE class='unknown_send' AND resolved=0").fetchall()
            row=next((q for q in queues if self.store.queue_ident(q)==queue_id),None)
            if row is None:
                raise ValueError('No pending unknown-send queue item')
            send=conn.execute("SELECT * FROM sends WHERE message_id=? AND prospect_id=? AND status='unknown'",
                              (row['source'],row['prospect_id'])).fetchone()
            if send is None:
                raise ValueError('Queue item does not identify an unknown send')
            self._settle_unknown(send,outcome,at)
            conn.execute('INSERT INTO audit(at,action,detail) VALUES(?,?,?)',
                         (stamp(at),'owner_unknown_send',json.dumps({'queue':queue_id,'send_id':send['id'],
                                                                  'outcome':outcome,'note':note.strip()})))

    def evaluate_bounces(self,at):
        with self.store.transaction() as conn:
            for m in conn.execute('SELECT * FROM mailboxes').fetchall():
                days={local_day(r[0]) for r in conn.execute("SELECT created FROM sends WHERE mailbox=? AND status='sent'",(m['id'],))}
                for day in days:
                    from datetime import datetime, time
                    end=datetime.combine(day+timedelta(days=1),time(),CENTRAL)
                    if instant(at)<instant(end)+timedelta(hours=72):
                        continue
                    key='bounce-evaluated:'+m['id']+':'+str(day)
                    if conn.execute('SELECT 1 FROM audit WHERE action=?',(key,)).fetchone():
                        continue
                    sent=[r for r in conn.execute("SELECT * FROM sends WHERE mailbox=? AND status='sent'",(m['id'],)) if local_day(r['created'])==day]
                    ids={r['id'] for r in sent}
                    bounced={r[0] for r in conn.execute("SELECT send_id FROM events WHERE kind='hard'") if r[0] in ids}
                    if len(sent)>=20 and len(bounced)/len(sent)>.05:
                        self._pause(m['id'],at,24)
                    conn.execute('INSERT INTO audit(at,action,detail) VALUES(?,?,?)',(stamp(at),key,json.dumps({'sent':len(sent),'bounced':len(bounced)})))

    def queue_owner_reply(self, queue_id, text, at, approved=False):
        if not approved:
            raise PermissionError('Explicit owner resolution required')
        with self.store.transaction() as conn:
            row=conn.execute('SELECT * FROM queue WHERE id=?',(queue_id,)).fetchone()
            if not row or row['resolved'] or not row['prospect_id'] or row['class']=='unknown_send':
                raise ValueError('Unresolved known-prospect queue item required')
            p=self.store.get(row['prospect_id']); p['mailbox']=self.mailbox(p)
            message=render(self.config,p,self.token(p['id']),'<'+uuid.uuid4().hex+'@'+self.config['sending_domain']+'>',owner_text=text)
            conn.execute('INSERT INTO sends(prospect_id,email_no,kind,mailbox,message_id,status,created,updated,attempt,template,body,not_before) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                         (p['id'],'owner:'+str(queue_id),'service',p['mailbox'],str(message['Message-ID']),'pending',stamp(at),stamp(at),0,'OWNER',message.as_string(),stamp(service_due(at,self.holidays))))
            conn.execute('UPDATE queue SET resolved=1 WHERE id=?',(queue_id,))
            self.store.save(p)

    def regenerate_batch(self,ids,at,remove_old):
        """Caller removes old deployments before admitting NEW slugs; never re-date old ones."""
        old=[self.store.get(i) for i in ids]
        if any(p.get('first_send_at') for p in old):
            raise ValueError('Cannot regenerate a contacted batch')
        if remove_old([p['preview_slug'] for p in old]) is not True:
            raise ValueError('Old-preview removal not confirmed')
        batch=uuid.uuid4().hex[:12]
        with self.store.transaction() as conn:
            for p in old:
                p['preview_slug']=p['id']+'-'+batch
                p['generated_at']=stamp(at); p['expiry_utc']=stamp(expiry(at)); self.store.save(p)
            conn.execute('INSERT INTO audit(at,action,detail) VALUES(?,?,?)',(stamp(at),'new_batch',json.dumps({'ids':ids,'batch':batch})))
        return [self.store.get(i) for i in ids]
