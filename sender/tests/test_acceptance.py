"""Twenty numbered acceptance fixtures from outreach section 9, as amended."""
from datetime import datetime, timedelta, timezone
import json
from sender.calendar import due, stamp
from sender.rules import parse
from sender.templates import SIGNATURE, variables, fill
from sender.transports import FakeSMTP
from sender.tests.support import Fixture, AT, mail, dsn


class Acceptance(Fixture):
    def test_01_interested(self):
        r=self.receive('Yes, interested'); self.assertEqual(r['reply'],'ORDER')
        self.assertEqual(self.store.get('p1')['state'],'replied')
        self.assertEqual(self.engine.dispatch('p1',2,AT,FakeSMTP()),'state_or_suppression')

    def test_02_quoted_footer(self):
        footer=fill(SIGNATURE,variables(self.config,self.store.get('p1'),self.engine.token('p1')))
        r=self.receive('Yes, interested\n\n'+footer)
        self.assertEqual(r['reply'],'ORDER'); self.assertFalse(self.store.suppressed('owner@plumber.invalid'))

    def test_03_refund_question(self):
        r=self.receive('Can I have a refund?')
        self.assertEqual(r['queue'],['refund']); self.assertEqual(r['reply'],'ACK_REFUND')

    def test_04_amended_interest_and_refund(self):
        text='Interested, but I want a refund first'
        self.assertEqual(parse(mail(text))['flags'],{'INTERESTED','REFUND'})
        r=self.receive(text); self.assertEqual(r['reply'],'ACK_REFUND'); self.assertEqual(r['queue'],['refund'])

    def test_05_legal(self):
        r=self.receive('Stop. My lawyer will contact you.')
        self.assertEqual(r['queue'],['legal']); self.assertIsNone(r['reply'])
        self.assertTrue(self.store.suppressed('owner@plumber.invalid')); self.assertEqual(self.sends(),[])

    def test_06_unsubscribe_terminal(self):
        raw=mail('Please unsubscribe'); self.engine.receive(raw,AT); self.engine.receive(raw,AT)
        self.assertEqual(self.store.get('p1')['state'],'suppressed')
        self.assertEqual([r['template'] for r in self.sends()],['ACK_UNSUB'])

    def test_07_not_now(self):
        r=self.receive('Not now'); p=self.store.get('p1')
        self.assertEqual(r['reply'],'ACK_NOT_NOW'); self.assertEqual(p['state'],'not_now')
        self.assertEqual(p['not_now_until'],stamp(AT+timedelta(days=60)))

    def test_08_amended_temporary_negative(self):
        r=self.receive('Not interested right now')
        self.assertEqual(r['state'],'not_now'); self.assertEqual(r['reply'],'ACK_NOT_NOW')
        self.assertFalse(self.store.suppressed('owner@plumber.invalid'))

    def test_09_yesterday(self):
        r=self.receive('I saw it yesterday'); self.assertEqual(r['queue'],['other']); self.assertIsNone(r['reply'])

    def test_10_monthly_analytics(self):
        r=self.receive('Can you show my monthly analytics report?')
        self.assertEqual(r['reply'],'ACK_QUESTION'); self.assertEqual(r['queue'],['question'])

    def test_11_human_out_of_office_words(self):
        r=self.receive('I am back from out of office; how much?')
        self.assertEqual(r['reply'],'FAQ_REPLY'); self.assertEqual(r['faq'],['price'])

    def test_12_auto_response(self):
        r=self.receive('unsubscribe',headers={'Auto-Submitted':'auto-replied'})
        self.assertEqual(r['kind'],'auto'); self.assertEqual(self.store.get('p1')['state'],'active')
        self.assertEqual(self.sends(),[])

    def test_13_hard_dsn(self):
        self.engine.dispatch('p1',1,AT,FakeSMTP())
        r=self.engine.receive(dsn('owner@plumber.invalid'),AT)
        self.assertEqual(r['recipients'],['owner@plumber.invalid'])
        self.assertTrue(self.store.suppressed('owner@plumber.invalid'))
        self.assertFalse(self.store.suppressed('mailer-daemon@provider.invalid'))

    def test_14_soft_dsn_window(self):
        self.engine.dispatch('p1',1,AT,FakeSMTP())
        for i in range(2):
            self.engine.receive(dsn('owner@plumber.invalid','4.2.0'),AT-timedelta(days=40))
        self.engine.receive(dsn('owner@plumber.invalid','4.2.0'),AT)
        self.assertFalse(self.store.suppressed('owner@plumber.invalid'))
        self.assertEqual(self.store.conn.execute("SELECT COUNT(*) FROM events WHERE kind='soft' AND at>=?",(stamp(AT-timedelta(days=30)),)).fetchone()[0],1)

    def test_15_inbound_dedup(self):
        raw=mail('Yes, interested'); self.engine.receive(raw,AT)
        self.assertEqual(self.engine.receive(raw,AT)['kind'],'duplicate')
        self.assertEqual(len(self.sends()),1)

    def test_16_shared_domain(self):
        self.add('p2','owner@gmail.com'); self.receive('unsubscribe',address='owner@gmail.com')
        self.assertTrue(self.store.suppressed('owner@gmail.com')); self.assertFalse(self.store.suppressed('someone@gmail.com'))

    def test_17_scanner_get(self):
        from sender.optout import local_server
        import threading,urllib.request
        server=local_server(self.engine,clock=lambda:AT)
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        try:
            url=f'http://127.0.0.1:{server.server_port}/unsubscribe/{self.engine.token("p1")}'
            with urllib.request.urlopen(url) as response:
                self.assertEqual(response.status,200)
            self.assertFalse(self.store.suppressed('owner@plumber.invalid'))
        finally:
            server.shutdown(); thread.join(); server.server_close()

    def test_18_calendar_and_holiday(self):
        p=self.store.get('p1'); p['first_send_at']=stamp(AT)
        self.assertEqual(due(p,3),datetime(2026,10,1,13,30,tzinfo=timezone.utc))
        self.assertIsNone(due(p,3,['2026-10-01']))
        self.assertEqual(self.store.get('p1')['expiry_utc'],p['expiry_utc'])

    def test_19_paid_webhook_twice(self):
        self.assertTrue(self.store.paid('order-1','p1',AT)); self.assertFalse(self.store.paid('order-1','p1',AT))
        self.assertEqual(self.store.conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0],1)
        self.assertEqual(self.store.get('p1')['state'],'paid')
        self.assertEqual(self.engine.dispatch('p1',2,AT,FakeSMTP()),'state_or_suppression')

    def test_20_legal_optout_after_ceiling(self):
        self.receive('Interested'); self.receive('How much?')
        r=self.receive('Unsubscribe. My lawyer will contact you.')
        self.assertIsNone(r['reply']); self.assertEqual(r['queue'],['legal'])
        row=self.store.conn.execute("SELECT * FROM suppression WHERE kind='email'").fetchone()
        self.assertEqual(set(json.loads(row['reasons'])),{'unsubscribe','legal'})
        self.assertEqual(self.store.get('p1')['state'],'suppressed')
