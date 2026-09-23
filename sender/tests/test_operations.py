from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import threading
import urllib.request
from sender.calendar import CENTRAL, due, stamp, expiry, next_slot, cap
from sender.gate import checks,validate
from sender.metrics import snapshot
from sender.optout import local_server
from sender.rules import FAQ,faq_matches
from sender.transports import FakeSMTP,FakeIMAP,SMTPAdapter,IMAPAdapter
from sender.tests.support import Fixture,AT,mail,dsn


class ExtraCases(Fixture):
    def test_extra_01_optout_interest(self):
        r=self.receive('Unsubscribe. I was interested.')
        self.assertEqual(r['reply'],'ACK_UNSUB'); self.assertEqual(r['state'],'suppressed')
        self.assertEqual(len(self.sends()),1)

    def test_extra_02_optout_refund(self):
        r=self.receive('Unsubscribe. Refund please.')
        self.assertEqual(r['reply'],'ACK_REFUND'); self.assertEqual(r['queue'],['refund'])
        self.assertEqual(r['state'],'suppressed'); self.assertEqual(len(self.sends()),1)

    def test_extra_03_plain_negative(self):
        r=self.receive('Not interested')
        self.assertEqual(r['reply'],'ACK_NEGATIVE'); self.assertEqual(r['state'],'suppressed')

    def test_extra_04_response_suppression_optout(self):
        r=self.receive('unsubscribe',headers={'X-Auto-Response-Suppress':'All'})
        self.assertEqual(r['state'],'suppressed'); self.assertIsNone(r['reply'])
        self.assertIn('reply_suppressed',r['queue']); self.assertEqual(self.sends(),[])

    def test_extra_05_dsn_without_outer_reference(self):
        self.engine.dispatch('p1',1,AT,FakeSMTP())
        raw=dsn('owner@plumber.invalid',original=self.sends()[0]['message_id'])
        self.engine.receive(raw,AT)
        self.assertTrue(self.store.suppressed('owner@plumber.invalid'))
        self.assertEqual(self.store.conn.execute("SELECT COUNT(*) FROM queue WHERE class='unknown_sender'").fetchone()[0],0)

    def test_extra_06_missing_message_id_once(self):
        raw=mail('unsubscribe',missing_id=True)
        self.engine.receive(raw,AT); self.assertEqual(self.engine.receive(raw,AT)['kind'],'duplicate')
        self.assertEqual(len(self.sends()),1)

    def test_extra_07_timeout_imap_found(self):
        smtp=FakeSMTP(['timeout_accepted'])
        self.assertEqual(self.engine.dispatch('p1',1,AT,smtp),'unknown')
        self.assertEqual(self.engine.dispatch('p1',2,AT,smtp),'held')
        self.engine.reconcile(AT+timedelta(minutes=30),FakeIMAP(smtp.sent))
        self.assertEqual(self.sends()[0]['status'],'sent')
        self.assertEqual(self.engine.dispatch('p1',1,AT+timedelta(minutes=31),smtp),'sent')
        self.assertEqual(len(smtp.accepted),1)


class Operations(Fixture):
    def test_tue_wed_thu_start_and_holiday(self):
        for start in (22,23,24):
            at=datetime(2026,9,start,13,30,tzinfo=timezone.utc)
            p=dict(generated_at=stamp(at),first_send_at=stamp(at),expiry_utc=stamp(expiry(at)))
            with self.subTest(start=start):
                third=due(p,3)
                self.assertIsNotNone(third); self.assertLess(third,expiry(at)-timedelta(hours=24))
                self.assertEqual(due(p,2).astimezone(CENTRAL).weekday(),1)

    def test_dst_wall_time(self):
        # Tuesday after spring/fall US transitions remains 08:30 Chicago.
        for utc in ('2026-03-10T13:30:00+00:00','2026-11-03T14:30:00+00:00'):
            at=datetime.fromisoformat(utc)
            self.assertEqual(next_slot(at),at); self.assertEqual(at.astimezone(CENTRAL).hour,8)
        before=datetime(2026,11,1,6,30,tzinfo=timezone.utc).astimezone(CENTRAL)
        after=datetime(2026,11,1,7,30,tzinfo=timezone.utc).astimezone(CENTRAL)
        self.assertEqual((before.hour,after.hour,before.fold,after.fold),(1,1,0,1))

    def test_optout_post_idempotent_and_send_refused(self):
        server=local_server(self.engine,clock=lambda:AT)
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        try:
            url=f'http://127.0.0.1:{server.server_port}/unsubscribe/{self.engine.token("p1")}'
            for _ in range(2):
                request=urllib.request.Request(url,data=b'List-Unsubscribe=One-Click',method='POST')
                with urllib.request.urlopen(request) as response:
                    self.assertEqual(response.status,200)
                    self.assertEqual(response.geturl(),url)
                    self.assertIsNone(response.headers.get('Set-Cookie'))
                    self.assertIn(b'Done',response.read())
            self.assertEqual(self.store.conn.execute('SELECT COUNT(*) FROM suppression').fetchone()[0],1)
            self.assertEqual(self.engine.dispatch('p1',1,AT,FakeSMTP()),'state_or_suppression')
            self.assertEqual(self.sends(),[])
        finally:
            server.shutdown(); thread.join(); server.server_close()

    def test_stale_batch_new_slugs_and_old_removal(self):
        p=self.store.get('p1'); old=AT-timedelta(days=2)
        p['generated_at']=stamp(old); p['expiry_utc']=stamp(expiry(old)); self.store.save(p)
        self.assertEqual(self.engine.dispatch('p1',1,AT,FakeSMTP()),'regenerate_batch')
        with self.assertRaises(ValueError):
            self.engine.regenerate_batch(['p1'],AT,lambda slugs:False)
        self.assertEqual(self.store.get('p1')['expiry_utc'],p['expiry_utc'])
        removed=[]
        def remove(slugs):
            removed.extend(slugs); return True
        fresh=self.engine.regenerate_batch(['p1'],AT,remove)[0]
        self.assertEqual(removed,[p['preview_slug']]); self.assertNotEqual(fresh['preview_slug'],p['preview_slug'])
        self.assertEqual(fresh['expiry_utc'],stamp(expiry(AT)))

    def test_intent_durable_after_process_loss(self):
        smtp=FakeSMTP(['crash'])
        with self.assertRaises(KeyboardInterrupt):
            self.engine.dispatch('p1',1,AT,smtp)
        self.assertEqual(self.sends()[0]['status'],'sending')
        # A separate database connection observes the committed intent.
        import sqlite3
        conn=sqlite3.connect(Path(self.temp.name)/'sender.sqlite')
        try:
            self.assertEqual(conn.execute('SELECT status FROM sends').fetchone()[0],'sending')
        finally:
            conn.close()
        self.engine.reconcile(AT+timedelta(minutes=30),FakeIMAP(smtp.sent))
        self.assertEqual(self.sends()[0]['status'],'sent'); self.assertEqual(len(smtp.accepted),1)

    def test_imap_unavailable_does_not_mean_failed(self):
        self.engine.dispatch('p1',1,AT,FakeSMTP(['timeout']))
        self.engine.reconcile(AT+timedelta(days=2),FakeIMAP(available=False))
        self.assertEqual(self.sends()[0]['status'],'unknown')

    def test_exactly_one_retry_on_definite_failure(self):
        smtp=FakeSMTP(['failed','failed'])
        self.assertEqual(self.engine.dispatch('p1',1,AT,smtp),'failed')
        self.assertEqual(self.engine.dispatch('p1',1,AT,smtp),'failed')
        self.assertEqual(self.engine.dispatch('p1',1,AT,smtp),'retry_exhausted')
        self.assertEqual(self.sends()[0]['attempt'],2)

    def test_daily_cap_includes_unknown_intents(self):
        self.store.conn.execute('UPDATE mailboxes SET first_send=?',(stamp(AT),))
        smtp=FakeSMTP(['timeout']*10)
        for i in range(11):
            ident=f'cap{i}'; self.add(ident,f'owner@{ident}.invalid')
            result=self.engine.dispatch(ident,1,AT,smtp)
            self.assertEqual(result,'unknown' if i<10 else 'daily_cap')

    def test_domain_cap_across_mailboxes(self):
        smtp=FakeSMTP()
        for i in range(6):
            ident=f'domain{i}'; self.add(ident,f'user{i}@sharedbusiness.invalid',mailbox=['hello','team','hi'][i%3])
            self.assertEqual(self.engine.dispatch(ident,1,AT,smtp),'sent' if i<5 else 'domain_cap')

    def test_replies_priority_and_suppressed_service_allowed(self):
        r=self.receive('unsubscribe'); job=self.sends()[0]['email_no']
        self.add('p2','owner@else.invalid')
        self.assertEqual(self.engine.dispatch('p2',1,AT,FakeSMTP()),'service_priority')
        self.assertEqual(self.engine.dispatch('p1',0,AT,FakeSMTP(),service_job=job),'sent')
        self.assertEqual(self.store.get('p1')['state'],'suppressed')

    def test_role_region_and_expiry_recheck(self):
        self.add('role','privacy@business.invalid'); self.add('region','owner@other.invalid',region='London')
        self.assertEqual(self.engine.dispatch('role',1,AT,FakeSMTP()),'role_address')
        self.assertEqual(self.engine.dispatch('region',1,AT,FakeSMTP()),'region')
        p=self.store.get('p1'); p['expiry_utc']=stamp(AT+timedelta(hours=23)); self.store.save(p)
        self.assertEqual(self.engine.dispatch('p1',1,AT,FakeSMTP()),'expired')

    def test_faq_all_eight_and_first_occurrence(self):
        for key,(words,_) in FAQ.items():
            with self.subTest(key=key):
                self.assertIn(key,faq_matches(words[0]+'?'))
        self.assertEqual(faq_matches('Photos, then price, then hosting?'),['photos','price'])

    def test_reply_limit_and_transactional_exceptions(self):
        self.receive('Interested'); self.receive('Price?')
        r=self.receive('Hosting?'); self.assertIsNone(r['reply']); self.assertIn('reply_ceiling',r['queue'])
        r=self.receive('Refund please'); self.assertEqual(r['reply'],'ACK_REFUND')

    def test_paid_terminal_and_refund(self):
        self.store.paid('o1','p1',AT)
        self.receive('Unsubscribe. Refund please.')
        self.assertEqual(self.store.get('p1')['state'],'paid')
        self.assertTrue(self.store.suppressed('owner@plumber.invalid'))

    def test_complaint_pause_and_disable(self):
        self.receive('I reported this spam')
        row=self.store.conn.execute("SELECT * FROM mailboxes WHERE id='hello'").fetchone()
        self.assertEqual(row['pause_until'],stamp(AT+timedelta(hours=24)))
        self.receive('I reported this spam again')
        self.assertEqual(self.store.conn.execute("SELECT disabled FROM mailboxes WHERE id='hello'").fetchone()[0],1)

    def test_three_soft_bounces_and_dedup(self):
        self.engine.dispatch('p1',1,AT,FakeSMTP())
        for i in range(3):
            raw=dsn('owner@plumber.invalid','4.2.0'); self.engine.receive(raw,AT); self.engine.receive(raw,AT)
        self.assertTrue(self.store.suppressed('owner@plumber.invalid'))
        self.assertEqual(self.store.conn.execute("SELECT COUNT(*) FROM events WHERE kind='soft'").fetchone()[0],3)

    def test_metrics_dedup_and_unknown_views(self):
        self.engine.dispatch('p1',1,AT,FakeSMTP()); self.receive('Interested'); self.receive('How much?')
        self.store.paid('a','p1',AT); self.store.paid('b','p1',AT); self.store.paid('a','p1',AT)
        self.add('internal','staff@example.invalid',test=True)
        self.engine.dispatch('internal',1,AT,FakeSMTP())
        result=snapshot(self.store,AT+timedelta(days=1))
        self.assertEqual(result['emails_sent'],1); self.assertEqual(result['replies'],1)
        self.assertEqual(result['reply_messages'],2); self.assertIsNone(result['sample_views'])
        self.assertEqual(result['paid'],2); self.assertEqual(result['cohort']['paid_prospects'],1)
        self.assertEqual(result['rates']['paid'],1)

    def test_queue_projection_idempotent(self):
        self.receive('My attorney will contact you')
        self.store.project_queue(self.temp.name,AT); self.store.project_queue(self.temp.name,AT)
        content=(Path(self.temp.name)/'approvals/pending.md').read_text()
        self.assertEqual(content.count('- [ ]'),1)
        self.assertEqual(len(list((Path(self.temp.name)/'sales/queue').glob('*.md'))),1)

    def test_gate_red_and_placeholder_validation(self):
        self.assertTrue(validate(self.config)); self.assertFalse(all(ok for _,ok in checks(self.config)))
        broken=dict(self.config,company='{COMPANY}')
        with self.assertRaises(ValueError): validate(broken)
        with self.assertRaises(PermissionError): self.engine.dispatch('p1',1,AT,SMTPAdapter(None))

    def test_mail_thread_headers_and_rendering(self):
        smtp=FakeSMTP(); self.engine.dispatch('p1',1,AT,smtp)
        body=smtp.accepted[0][1]
        self.assertIn('List-Unsubscribe-Post: List-Unsubscribe=One-Click',body)
        self.assertNotIn('{COMPANY}',body)
        p=self.store.get('p1'); msg=self.engine._message(p,number=2)
        self.assertEqual(msg['In-Reply-To'],p['thread_message_id']); self.assertTrue(msg['Subject'].startswith('Re: '))

    def test_imap_adapter_queries_exact_id_readonly(self):
        class Client:
            def select(client,folder,readonly):
                self.assertEqual(folder,'Sent'); self.assertTrue(readonly); return 'OK',[]
            def search(client,*args):
                self.assertEqual(args,(None,'HEADER','Message-ID','"<id@x>"')); return 'OK',[b'7']
        self.assertTrue(IMAPAdapter(Client(),'Sent').contains('hello','<id@x>'))
