from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
from pathlib import Path
import shutil
import sys
from sender.calendar import stamp,expiry
from sender.engine import Engine
from sender.metrics import export,record_view,snapshot
from sender.scheduler import tick
from sender.store import Store
from sender.transports import FakeSMTP,FakeIMAP
from sender.tests.support import Fixture,AT,dsn


class Integration(Fixture):
    def test_tick_sends_once_reconciles_every_thirty_minutes(self):
        smtp=FakeSMTP(); imap=FakeIMAP(smtp.sent)
        tick(self.engine,AT,smtp,imap); tick(self.engine,AT+timedelta(minutes=1),smtp,imap)
        self.assertEqual(len(smtp.accepted),1)
        self.assertEqual(self.store.conn.execute("SELECT COUNT(*) FROM audit WHERE action='reconcile_tick'").fetchone()[0],1)
        tick(self.engine,AT+timedelta(minutes=30),smtp,imap)
        self.assertEqual(self.store.conn.execute("SELECT COUNT(*) FROM audit WHERE action='reconcile_tick'").fetchone()[0],2)

    def test_two_workers_do_not_double_send(self):
        second=Store(Path(self.temp.name)/'sender.sqlite'); self.addCleanup(second.close)
        other=Engine(second,self.config,b'x'*32); smtp=FakeSMTP()
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs=[pool.submit(e.dispatch,'p1',1,AT,smtp) for e in (self.engine,other)]
            for job in jobs: job.result()
        self.assertEqual(len(smtp.accepted),1); self.assertEqual(len(self.sends()),1)

    def test_bounce_pause_after_seventy_two_hours(self):
        smtp=FakeSMTP()
        for i in range(20):
            self.add(f'bounce{i}',f'a@bounce{i}.invalid')
            self.assertEqual(self.engine.dispatch(f'bounce{i}',1,AT,smtp),'sent')
        for i in range(2): self.engine.receive(dsn(f'a@bounce{i}.invalid'),AT)
        self.engine.evaluate_bounces(AT+timedelta(days=2))
        self.assertIsNone(self.store.conn.execute("SELECT pause_until FROM mailboxes WHERE id='hello'").fetchone()[0])
        self.engine.evaluate_bounces(AT+timedelta(days=4))
        self.assertEqual(self.store.conn.execute("SELECT pause_until FROM mailboxes WHERE id='hello'").fetchone()[0],stamp(AT+timedelta(days=5)))

    def test_complaint_fifty_accepted_in_rolling_week(self):
        self.config['complaint_feed']=True
        smtp=FakeSMTP()
        for i in range(50):
            at=AT-timedelta(days=1) if i<25 else AT
            self.add(f'feedback{i}',f'a@feedback{i}.invalid',generated_at=stamp(at),expiry_utc=stamp(expiry(at)))
            self.assertEqual(self.engine.dispatch(f'feedback{i}',1,at,smtp),'sent')
        self.engine.feedback('feedback-event','feedback0',AT)
        row=self.store.conn.execute("SELECT * FROM mailboxes WHERE id='hello'").fetchone()
        self.assertEqual(row['pause_until'],stamp(AT+timedelta(hours=48)))
        self.assertEqual(row['disabled'],0)

    def test_owner_reply_needs_resolution_and_is_not_automatic(self):
        self.receive('My lawyer will contact you')
        ident=self.store.conn.execute('SELECT id FROM queue').fetchone()[0]
        with self.assertRaises(PermissionError): self.engine.queue_owner_reply(ident,'Received.',AT)
        self.assertEqual(self.sends(),[])
        self.engine.queue_owner_reply(ident,'Received.',AT,approved=True)
        row=self.sends()[0]; self.assertEqual(row['template'],'OWNER')
        self.assertEqual(self.engine.dispatch('p1',0,AT,FakeSMTP(),service_job=row['email_no']),'sent')
        self.assertEqual(self.store.get('p1')['state'],'suppressed')

    def test_views_exclude_bots_cidr_and_duplicate_events(self):
        self.engine.dispatch('p1',1,AT,FakeSMTP())
        self.config['analytics_exclude_ips']=['192.0.2.0/24']
        record_view(self.store,'own','p1',AT,'192.0.2.1',False,self.config)
        record_view(self.store,'bot','p1',AT,'198.51.100.1',True,self.config)
        self.assertEqual(snapshot(self.store,AT+timedelta(days=1),True)['sample_views'],0)
        for _ in range(2): record_view(self.store,'visitor','p1',AT,'198.51.100.1',False,self.config)
        self.assertEqual(snapshot(self.store,AT+timedelta(days=1),True)['sample_views'],1)
        self.assertEqual(self.store.conn.execute('SELECT COUNT(*) FROM views').fetchone()[0],3)

    def test_daily_report_reads_closed_day_preserves_na(self):
        project=Path(__file__).resolve().parents[2]
        repo=project; root=Path(self.temp.name)/'company'; root.mkdir()
        for name in ('company','agents','approvals','tasks','reviews'):
            shutil.copytree(repo/name,root/name)
        sys.path.insert(0,str(repo/'scripts'))
        from daily_report import generate,sender_pipeline
        self.engine.dispatch('p1',1,AT,FakeSMTP())
        report_at=AT+timedelta(days=1)
        export(self.store,report_at,root/'.runtime/sender/pipeline.json')
        text=generate(root,report_at).read_text(encoding='utf-8')
        self.assertIn('Central closed 2026-09-23:',text)
        self.assertIn('emails sent: 1 / replies: 0 / sample views: n/a / paid: 0',text)
        self.assertLessEqual(len(text.splitlines()),30)
        with self.assertRaisesRegex(ValueError,'stale'):
            sender_pipeline(root,report_at+timedelta(days=1))
