from datetime import datetime, timedelta, timezone
from email.message import EmailMessage, Message
from email.utils import format_datetime
from pathlib import Path
import tempfile
import unittest
import uuid

from sender.calendar import stamp, expiry
from sender.engine import Engine
from sender.rules import SHARED
from sender.store import Store

AT=datetime(2026,9,23,13,30,tzinfo=timezone.utc)


def config():
    return dict(company='Example Team',postal_address='1 Test Lane',sending_domain='outreach.example.invalid',
                mailboxes=['hello','team','hi'],auth_passed=['hello','team','hi'],
                preview_base_url='https://preview.example.invalid/previews',unsub_base_url='https://example.invalid/unsubscribe',
                checkout_base_url='https://checkout.example.invalid',target_regions=['Houston, TX'],
                internal_domains=['outreach.example.invalid','example.invalid'],shared_mail_domains=sorted(SHARED),
                us_federal_holidays=[],owner_queue_path='approvals/pending.md',complaint_feed=False,analytics_exclude_ips=[])


def mail(body,ident=None,address='owner@plumber.invalid',headers=None,missing_id=False):
    m=EmailMessage(); m['From']=address; m['To']='hello@outreach.example.invalid'
    m['Date']=format_datetime(AT)
    if not missing_id:
        m['Message-ID']=ident or '<'+uuid.uuid4().hex+'@plumber.invalid>'
    for key,value in (headers or {}).items():
        m[key]=value
    m.set_content(body)
    return m.as_bytes()


def dsn(address,status='5.1.1',ident=None,original=None):
    m=EmailMessage(); m['From']='mailer-daemon@provider.invalid'; m['To']='hello@outreach.example.invalid'
    m['Message-ID']=ident or '<'+uuid.uuid4().hex+'@provider.invalid>'
    m.set_type('multipart/report'); m.set_param('report-type','delivery-status')
    report=EmailMessage(); report.set_type('message/delivery-status')
    header=Message(); header['Reporting-MTA']='dns; provider.invalid'
    recipient=Message(); recipient['Final-Recipient']='rfc822; '+address; recipient['Status']=status
    report.set_payload([header,recipient]); m.attach(report)
    if original:
        wrapper=EmailMessage(); wrapper.set_type('message/rfc822')
        original_message=EmailMessage(); original_message['Message-ID']=original
        original_message['To']=address; original_message.set_content('Original')
        wrapper.set_payload([original_message]); m.attach(wrapper)
    return m.as_bytes()


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store=Store(Path(self.temp.name)/'sender.sqlite')
        self.addCleanup(self.store.close)
        self.config=config(); self.engine=Engine(self.store,self.config,b'x'*32)
        self.store.conn.execute('UPDATE mailboxes SET first_send=?',(stamp(AT-timedelta(days=30)),))
        self.add()

    def add(self,ident='p1',email='owner@plumber.invalid',**kw):
        generated=AT-timedelta(hours=2)
        p=dict(id=ident,email=email,business='Fixture Plumbing',city='Houston',region='Houston, TX',
               generated_at=stamp(generated),expiry_utc=stamp(expiry(generated)),preview_slug=ident+'-preview',state='active',mailbox='hello')
        p.update(kw); self.store.add(p); return p

    def receive(self,body,**kw):
        return self.engine.receive(mail(body,**kw),AT)

    def sends(self):
        return self.store.conn.execute('SELECT * FROM sends ORDER BY id').fetchall()
