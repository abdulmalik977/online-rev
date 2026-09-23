"""Owner-approved A7: unknown delivery, receipt clocks and full-message identity."""
from datetime import timedelta
from pathlib import Path
import smtplib
from email import policy
from email.parser import BytesParser

from sender.calendar import stamp, next_business_day
from sender.engine import Engine, DefiniteFailure
from sender.metrics import snapshot
from sender.rules import parse
from sender.transports import FakeSMTP, FakeIMAP, SMTPAdapter
from sender.tests.support import Fixture, AT, mail


class AmendmentA7(Fixture):
    def unknown(self, outcome='timeout_accepted', sent_copy=False):
        smtp=FakeSMTP([outcome],sent_copy=sent_copy)
        self.assertEqual(self.engine.dispatch('p1',1,AT,smtp),'unknown')
        return smtp

    def test_unknown_stays_held_after_24_hours_and_a_week(self):
        smtp=self.unknown()
        for delta in (timedelta(hours=24),timedelta(days=7)):
            self.engine.reconcile(AT+delta,FakeIMAP())
            self.assertEqual(self.sends()[0]['status'],'unknown')
            self.assertEqual(self.engine.dispatch('p1',2,AT+delta,smtp),'held')
        self.assertEqual(len(smtp.accepted),1)
        self.assertEqual(self.store.conn.execute("SELECT COUNT(*) FROM queue WHERE class='unknown_send'").fetchone()[0],1)

    def test_unknown_queue_has_required_stable_id_and_receipt_deadline(self):
        self.unknown(); self.engine.reconcile(AT+timedelta(days=2),FakeIMAP())
        q=self.store.conn.execute("SELECT * FROM queue WHERE class='unknown_send'").fetchone()
        self.assertEqual(q['created'],stamp(AT))
        self.assertEqual(q['due'],stamp(next_business_day(AT)))
        self.store.project_queue(self.temp.name,AT)
        path=Path(self.temp.name)/'sales/queue/Q-p1-unknown-send.md'
        self.assertTrue(path.exists())
        self.assertIn(self.sends()[0]['message_id'],path.read_text(encoding='utf-8'))

    def test_late_imap_found_closes_queue_without_resend(self):
        smtp=self.unknown(); ident=self.sends()[0]['message_id']
        self.engine.reconcile(AT+timedelta(days=3),FakeIMAP({ident}))
        self.assertEqual(self.sends()[0]['status'],'sent')
        self.assertEqual(self.store.get('p1')['first_send_at'],stamp(AT))
        self.assertEqual(self.store.conn.execute("SELECT resolved FROM queue WHERE class='unknown_send'").fetchone()[0],1)
        self.assertEqual(self.engine.dispatch('p1',1,AT+timedelta(days=3),smtp),'sent')
        self.assertEqual(len(smtp.accepted),1)

    def test_owner_reconciliation_requires_explicit_approval_and_evidence_note(self):
        self.unknown()
        with self.assertRaises(PermissionError):
            self.engine.resolve_unknown_send('Q-p1-unknown-send',AT,'failed',note='Provider confirms no acceptance')
        with self.assertRaises(ValueError):
            self.engine.resolve_unknown_send('Q-p1-unknown-send',AT,'failed',approved=True,note='')
        self.assertEqual(self.sends()[0]['status'],'unknown')
        self.engine.resolve_unknown_send('Q-p1-unknown-send',AT,'failed',approved=True,note='Owner reconciled with provider; no acceptance')
        self.assertEqual(self.sends()[0]['status'],'failed')
        self.assertEqual(self.engine.dispatch('p1',1,AT,FakeSMTP(['failed'])),'failed')
        self.assertEqual(self.engine.dispatch('p1',1,AT,FakeSMTP()),'retry_exhausted')
        self.assertEqual(self.store.conn.execute("SELECT COUNT(*) FROM audit WHERE action='owner_unknown_send'").fetchone()[0],1)

    def test_owner_sent_outcome_and_queue_cannot_be_used_as_customer_reply(self):
        smtp=self.unknown()
        q=self.store.conn.execute("SELECT id FROM queue WHERE class='unknown_send'").fetchone()[0]
        with self.assertRaises(ValueError):
            self.engine.queue_owner_reply(q,'Retry approved',AT,approved=True)
        self.engine.resolve_unknown_send('Q-p1-unknown-send',AT,'sent',approved=True,note='Owner confirmed accepted delivery')
        self.assertEqual(self.engine.dispatch('p1',1,AT,smtp),'sent')
        self.assertEqual(len(self.sends()),1)
        self.store.project_queue(self.temp.name,AT)
        self.assertNotIn('- [ ] Q-p1-unknown-send |',(Path(self.temp.name)/'approvals/pending.md').read_text())

    def test_paid_and_suppressed_still_prevent_retry_after_owner_resolution(self):
        for state in ('paid','suppressed'):
            with self.subTest(state=state):
                ident='terminal-'+state
                self.add(ident,f'owner@{state}.invalid')
                self.engine.dispatch(ident,1,AT,FakeSMTP(['timeout']))
                p=self.store.get(ident); p['state']=state; self.store.save(p)
                self.engine.resolve_unknown_send('Q-'+ident+'-unknown-send',AT,'failed',approved=True,note='Explicit reconciliation')
                self.assertEqual(self.engine.dispatch(ident,1,AT,FakeSMTP()),'state_or_suppression')

    def test_all_owner_deadlines_use_receipt_not_payment(self):
        p=self.store.get('p1'); p['payment_at']=stamp(AT-timedelta(days=10)); p['confirmation_at']=stamp(AT+timedelta(days=10)); self.store.save(p)
        self.engine.receive(mail('My lawyer will contact you'),AT)
        self.engine.receive(mail('Unknown sender',address='someone@unknown.invalid'),AT)
        for row in self.store.conn.execute('SELECT * FROM queue'):
            self.assertEqual(row['due'],stamp(next_business_day(AT)))
        self.assertEqual(self.store.get('p1')['confirmation_at'],p['confirmation_at'])

    def test_queue_clock_holiday_and_overdue_metrics(self):
        self.config['us_federal_holidays']=['2026-09-24']
        engine=Engine(self.store,self.config,b'x'*32)
        engine.receive(mail('My lawyer will contact you'),AT)
        row=self.store.conn.execute('SELECT * FROM queue').fetchone()
        self.assertEqual(row['due'],stamp(AT+timedelta(days=2)))
        report=snapshot(self.store,AT+timedelta(days=2,minutes=1))
        self.assertIn('Owner queue overdue: Q-p1-'+str(row['id']),report['critical'])

    def test_pending_legacy_queue_deadline_backfilled_without_resetting_receipt(self):
        self.receive('My lawyer will contact you')
        self.store.conn.execute('UPDATE queue SET due=NULL')
        Engine(self.store,self.config,b'x'*32)
        row=self.store.conn.execute('SELECT * FROM queue').fetchone()
        self.assertEqual(row['created'],stamp(AT)); self.assertEqual(row['due'],stamp(next_business_day(AT)))

    def test_missing_id_namespaced_by_mailbox_and_provider_uid(self):
        raw=mail('Question',missing_id=True)
        key=lambda box,uid: parse(raw,mailbox_id=box,provider_uid=uid)['id']
        self.assertEqual(key('hello','v1:42'),key('hello','v1:42'))
        self.assertNotEqual(key('hello','v1:42'),key('team','v1:42'))
        self.assertNotEqual(key('hello','v1:42'),key('hello','v1:43'))
        self.assertNotEqual(key('hello',None),key('hello','v1:42'))
        self.assertEqual(self.engine.receive(raw,AT,mailbox_id='hello',provider_uid='v1:42')['kind'],'human')
        self.assertEqual(self.engine.receive(raw,AT,mailbox_id='hello',provider_uid='v1:42')['kind'],'duplicate')

    def test_canonical_line_endings_and_complete_mime_content(self):
        raw=mail('a'*600+'\nunsubscribe',missing_id=True)
        self.assertEqual(parse(raw,mailbox_id='hello')['id'],parse(raw.replace(b'\n',b'\r\n'),mailbox_id='hello')['id'])
        message=BytesParser(policy=policy.default).parsebytes(raw)
        message.add_attachment(b'first attachment',maintype='application',subtype='octet-stream',filename='x.bin')
        first=message.as_bytes(); second=first.replace(b'Zmlyc3QgYXR0YWNobWVudA==',b'c2Vjb25kIGF0dGFjaG1lbnQ=')
        self.assertNotEqual(first,second)
        self.assertNotEqual(parse(first,mailbox_id='hello')['id'],parse(second,mailbox_id='hello')['id'])

    def test_missing_id_requires_receiver_context(self):
        with self.assertRaises(ValueError): self.engine.receive(mail('unsubscribe',missing_id=True),AT)
        with self.assertRaises(ValueError): self.engine.receive(mail('unsubscribe',missing_id=True),AT,mailbox_id='not-configured')

    def test_unknown_retry_reopens_same_queue_and_updates_projection(self):
        self.unknown()
        self.store.project_queue(self.temp.name,AT)
        self.engine.resolve_unknown_send('Q-p1-unknown-send',AT,'failed',approved=True,note='Owner reconciled initial outcome')
        self.store.project_queue(self.temp.name,AT)
        path=Path(self.temp.name)/'approvals/pending.md'
        self.assertIn('- [x] Q-p1-unknown-send |',path.read_text())
        later=AT+timedelta(minutes=1)
        self.assertEqual(self.engine.dispatch('p1',1,later,FakeSMTP(['timeout'])),'unknown')
        self.store.project_queue(self.temp.name,later)
        text=path.read_text()
        self.assertEqual(text.count('Q-p1-unknown-send |'),1)
        self.assertIn('- [ ] Q-p1-unknown-send |',text)
        row=self.store.conn.execute("SELECT * FROM queue WHERE class='unknown_send'").fetchone()
        self.assertEqual(row['created'],stamp(later))
        self.assertEqual(row['due'],stamp(next_business_day(later)))
        self.engine.resolve_unknown_send('Q-p1-unknown-send',later,'failed',approved=True,note='Owner reconciled retry too')
        self.assertEqual(self.engine.dispatch('p1',1,later,FakeSMTP()),'retry_exhausted')

    def test_imap_unavailable_keeps_owner_queue_and_hold(self):
        self.unknown()
        self.engine.reconcile(AT+timedelta(days=3),FakeIMAP(available=False))
        self.assertEqual(self.sends()[0]['status'],'unknown')
        self.assertEqual(self.store.conn.execute("SELECT resolved FROM queue WHERE class='unknown_send'").fetchone()[0],0)
        self.assertEqual(self.engine.dispatch('p1',2,AT+timedelta(days=3),FakeSMTP()),'held')

    def test_receipt_clock_crosses_weekend_and_dst(self):
        from datetime import datetime, timezone
        receipt=datetime(2026,10,30,13,30,tzinfo=timezone.utc)  # Friday 08:30 CDT.
        expected=datetime(2026,11,2,14,30,tzinfo=timezone.utc)  # Monday 08:30 CST.
        self.assertEqual(next_business_day(receipt),expected)

    def test_smtp_rejections_are_definite_but_disconnection_is_ambiguous(self):
        class Client:
            def __init__(self,error): self.error=error
            def send_message(self,message): raise self.error
        body=mail('hello').decode()
        for error in (smtplib.SMTPDataError(451,b'temporary rejection'),smtplib.SMTPDataError(550,b'rejected'),ConnectionRefusedError('before DATA')):
            with self.subTest(error=type(error).__name__):
                with self.assertRaises(DefiniteFailure): SMTPAdapter(Client(error)).send('<id@x>',body)
        with self.assertRaises(smtplib.SMTPServerDisconnected):
            SMTPAdapter(Client(smtplib.SMTPServerDisconnected('response lost'))).send('<id@x>',body)
