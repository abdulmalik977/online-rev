import base64
from contextlib import contextmanager
from datetime import timedelta
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import zipfile

from orders.flow import Orders
from orders.http import local_server
from orders.lifecycle import FakeAdapter
from orders.tests import test_flow as base
ROOT,AT,SECRET=base.ROOT,base.AT,base.SECRET
from sender.engine import Engine
from sender.store import Store
from sender.tests.support import config as sender_config
from sender.transports import FakeSMTP


class LifecycleTests(unittest.TestCase):
    setUp=base.Flow.setUp
    pay=base.Flow.pay
    confirm=base.Flow.confirm
    def live(self):
        self.pay(); self.confirm(); self.store.promote('order-1')
        host=FakeAdapter(); self.store.launch('order-1',AT+timedelta(hours=2),host)
        return host

    def test_corrections_escape_html_and_do_not_reset_launch_clock(self):
        self.pay(); row=self.confirm(corrections='Please fix phone and hours')
        due=row['launch_due']
        with self.assertRaises(PermissionError): self.store.apply_change('order-1','fix',{'hours':'9-5'},AT,correction=True)
        self.store.apply_change('order-1','fix',{'phone':'+15555550199','hours':'<b>Mon-Fri 9-5</b>'},AT,verified=True,correction=True)
        folder=self.store.promote('order-1'); page=(folder/'index.html').read_text(encoding='utf-8')
        self.assertIn('&lt;b&gt;Mon-Fri 9-5&lt;/b&gt;',page)
        self.assertIn('+15555550199',page)
        self.assertEqual(self.store.get('order-1')['launch_due'],due)

    def test_launch_acknowledges_exact_artifact_and_refuses_live_adapter(self):
        self.pay(); self.confirm(); self.store.promote('order-1')
        host=FakeAdapter(); host.offline=False
        with self.assertRaises(PermissionError): self.store.launch('order-1',AT,host)
        self.assertIsNone(self.store.get('order-1')['live_at'])
        host.offline=True; receipt=self.store.launch('order-1',AT+timedelta(hours=2),host)
        self.assertTrue(receipt['https_verified']); self.assertEqual(self.store.get('order-1')['status'],'live')
        self.store.launch('order-1',AT+timedelta(hours=3),host)
        self.assertEqual(len(host.calls),1)

    def test_timeout_accepted_refund_reconciles_once_even_after_late_launch(self):
        self.pay(); row=self.confirm(); self.store.promote('order-1')
        at=AT+timedelta(days=8)
        provider=FakeAdapter(['timeout_accepted'])
        self.assertEqual(self.store.refund_overdue(at,provider),[])
        provider.lookup_available=False
        self.assertEqual(self.store.refund_overdue(at+timedelta(minutes=1),provider),[])
        self.assertEqual(len(provider.calls),1)
        self.store.launch('order-1',at,FakeAdapter())
        self.assertEqual(len(self.store.refund_candidates(at)),1)
        provider.lookup_available=True
        self.assertEqual(self.store.refund_overdue(at+timedelta(minutes=2),provider),['order-1'])
        self.assertEqual(self.store.refund_overdue(at+timedelta(days=1),provider),[])
        self.assertEqual(len(provider.accepted),1); self.assertEqual(len(provider.calls),1)

    def test_timely_launch_has_no_automatic_refund(self):
        self.live(); provider=FakeAdapter()
        self.assertEqual(self.store.refund_overdue(AT+timedelta(days=30),provider),[])
        self.assertEqual(provider.calls,[])

    def test_cancellation_keeps_site_until_paid_period_and_sends_export_once(self):
        host=self.live(); end=AT+timedelta(days=30); provider=FakeAdapter(); mailer=FakeAdapter()
        with self.assertRaises(PermissionError): self.store.set_period_end('order-1',end)
        self.store.set_period_end('order-1',end,verified=True)
        self.store.cancel('order-1',AT+timedelta(days=1),provider,verified=True)
        with self.assertRaises(ValueError): self.store.finish_cancel('order-1',end-timedelta(seconds=1),host,mailer)
        self.assertEqual(self.store.get('order-1')['status'],'cancel_pending')
        self.store.finish_cancel('order-1',end,host,mailer)
        self.store.finish_cancel('order-1',end+timedelta(hours=1),host,mailer)
        self.assertEqual(self.store.get('order-1')['status'],'cancelled')
        self.assertEqual(len(mailer.accepted),1); self.assertIn('remove:order-1',host.accepted)
        export=self.store.db.execute("SELECT path FROM exports WHERE purpose='cancellation'").fetchone()[0]
        with zipfile.ZipFile(self.store.root/export) as z:
            self.assertEqual(set(z.namelist()),{'index.html','privacy.html','style.css','house.svg','_headers'})

    def test_maintenance_cap_idempotency_and_revision_are_enforced(self):
        self.live()
        for i in range(5):
            self.store.apply_change('order-1','update-'+str(i),{'hours':f'Hours {i}'},AT+timedelta(days=1),verified=True)
        self.store.apply_change('order-1','update-0',{'hours':'Hours 0'},AT+timedelta(days=1),verified=True)
        with self.assertRaises(ValueError): self.store.apply_change('order-1','sixth',{'hours':'More'},AT+timedelta(days=1),verified=True)
        with self.assertRaises(ValueError): self.store.apply_change('order-1','large',{'hours':'More'},AT,verified=True,minutes=31)
        folder=self.store.promote('order-1')
        self.assertTrue(folder.name.endswith('-r5'))
        self.assertTrue((self.store.root/'customers'/self.slug/'index.html').exists())
        self.store.launch('order-1',AT+timedelta(days=1,hours=2),FakeAdapter())
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM changes WHERE state='completed'").fetchone()[0],5)
        self.store.apply_change('order-1','new-month',{'hours':'New month'},AT+timedelta(days=31),verified=True)

    def test_photo_permission_and_private_export_allowlist(self):
        self.live()
        png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l9sAAAAASUVORK5CYII=')
        (self.store.root/'photo.png').write_bytes(png)
        photo={'path':'photo.png','consent':False,'alt':'Customer-owned photo'}
        with self.assertRaises(ValueError): self.store.apply_change('order-1','photo',{'photo':photo},AT,verified=True)
        photo['consent']=True
        self.store.apply_change('order-1','photo',{'photo':photo},AT,verified=True)
        folder=self.store.promote('order-1'); exported=self.store.export_site('order-1',AT)
        with zipfile.ZipFile(exported['path']) as z: self.assertTrue(any(name.endswith('.png') for name in z.namelist()))
        (folder/'orders.sqlite').write_text('private')
        with self.assertRaises(ValueError): self.store.export_site('order-1',AT)

    def test_weekly_exports_30_day_retention_does_not_touch_unrelated_files(self):
        self.live(); self.store.weekly_exports(AT)
        first=self.store.db.execute("SELECT path FROM exports WHERE purpose='weekly'").fetchone()[0]
        unrelated=self.store.root/'exports/unrelated.txt'; unrelated.write_text('keep')
        self.assertEqual(self.store.weekly_exports(AT+timedelta(days=6)),[])
        self.store.weekly_exports(AT+timedelta(days=30))
        self.assertTrue((self.store.root/first).exists())
        self.store.weekly_exports(AT+timedelta(days=31))
        self.assertFalse((self.store.root/first).exists()); self.assertEqual(unrelated.read_text(),'keep')

    def test_welcome_and_enquiry_forwarding_are_idempotent(self):
        self.live(); mailer=FakeAdapter(['timeout_accepted'])
        self.assertIsNone(self.store.send_welcome('order-1',AT,mailer))
        self.assertIsNotNone(self.store.send_welcome('order-1',AT+timedelta(minutes=1),mailer))
        self.store.enquiry('req',self.slug,AT,name='Visitor',email='visitor@example.invalid',message='Please help')
        self.assertEqual(self.store.forward_enquiries(AT,mailer),['req'])
        self.assertEqual(self.store.forward_enquiries(AT,mailer),[])
        self.assertEqual(len(mailer.accepted),2)
        payload=json.loads(self.store.db.execute("SELECT payload FROM effects WHERE key='welcome:order-1'").fetchone()[0])
        self.assertNotIn('private unsent draft',payload['body'])
        self.assertIn('Cancel anytime',payload['body'])

    def test_paid_bridge_blocks_outreach_and_recovers_after_cross_db_gap(self):
        sender=Store(self.root/'sender.sqlite'); self.addCleanup(sender.close)
        sender.add(dict(id='p1',email='buyer@example.invalid',preview_slug=self.slug,state='active',mailbox='hello',
                        business='Fixture Plumbing',city='Houston',region='Houston, TX',generated_at=(AT-timedelta(hours=1)).isoformat(),expiry_utc=(AT+timedelta(days=13)).isoformat()))
        engine=Engine(sender,sender_config(),SECRET)
        self.store.wire_sender(engine)
        # Simulate payment committed but crash before paid projection. Sender's guard reads the authoritative order DB.
        self.store.sender=None; self.pay()
        self.assertEqual(sender.get('p1')['state'],'active')
        smtp=FakeSMTP()
        self.assertEqual(engine.dispatch('p1',1,AT,smtp),'state_or_suppression')
        self.assertEqual(smtp.accepted,[]); self.assertTrue(sender.suppressed('buyer@example.invalid'))
        self.store.wire_sender(engine); self.pay()
        self.assertEqual(sender.conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0],1)
        self.assertEqual(self.store.fulfilment('order-1')['sender_synced'],1)

    def test_adapter_failure_retry_and_process_loss(self):
        self.pay()
        adapter=FakeAdapter(['failed'])
        self.assertIsNone(self.store.send_welcome('order-1',AT,adapter))
        self.assertIsNotNone(self.store.send_welcome('order-1',AT+timedelta(minutes=1),adapter))
        self.assertEqual(len(adapter.calls),2)
        # Crash after intent but before dispatch: fresh inflight is held, old intent reconciles.
        with self.store.db:
            self.store.db.execute("UPDATE effects SET state='inflight',receipt=NULL,attempts=1,updated=? WHERE key='welcome:order-1'",(AT.isoformat(),))
        self.assertIsNone(self.store.send_welcome('order-1',AT+timedelta(minutes=1),adapter))
        self.assertIsNotNone(self.store.send_welcome('order-1',AT+timedelta(minutes=6),adapter))
        self.assertEqual(len(adapter.calls),2)


    def test_cancellation_before_confirmation_exports_without_publishing(self):
        self.pay(); end=AT+timedelta(days=30)
        self.store.set_period_end('order-1',end,verified=True)
        self.store.cancel('order-1',AT,FakeAdapter(),verified=True)
        with self.assertRaises(ValueError): self.store.promote('order-1')
        host=FakeAdapter(); self.store.finish_cancel('order-1',end,host,FakeAdapter())
        self.assertEqual(self.store.get('order-1')['status'],'cancelled')
        self.assertIsNone(self.store.get('order-1')['live_at'])
        self.assertNotIn('publish:order-1:0',host.accepted)

    def test_unknown_launch_receipt_preserves_actual_on_time_publication(self):
        self.pay(); self.confirm(); self.store.promote('order-1')
        host=FakeAdapter(['timeout_accepted']); early=AT+timedelta(hours=2)
        self.assertIsNone(self.store.launch('order-1',early,host))
        provider=FakeAdapter()
        self.store.tick(AT+timedelta(days=8),provider=provider,host=host,mailer=FakeAdapter())
        self.assertEqual(self.store.get('order-1')['live_at'],early.isoformat())
        self.assertEqual(provider.calls,[])
        self.assertEqual(len(host.calls),1)

    def test_monthly_report_keeps_unavailable_visits_as_na(self):
        self.live(); mailer=FakeAdapter()
        with self.assertRaises(ValueError): self.store.monthly_report('order-1','2026-09',AT,mailer)
        self.store.monthly_report('order-1','2026-09',AT+timedelta(days=30),mailer)
        row=self.store.db.execute("SELECT payload FROM effects WHERE key='monthly:order-1:2026-09'").fetchone()
        self.assertIn('n/a',json.loads(row[0])['body'])
        self.store.monthly_report('order-1','2026-09',AT+timedelta(days=31),mailer)
        self.assertEqual(len(mailer.calls),1)

    def test_payment_cancels_queued_sales_reply_but_allows_refund_ack(self):
        from sender.tests.support import mail
        sender=Store(self.root/'sender.sqlite'); self.addCleanup(sender.close)
        sender.add(dict(id='p1',email='buyer@example.invalid',preview_slug=self.slug,state='active',mailbox='hello',
                        business='Fixture Plumbing',city='Houston',region='Houston, TX',generated_at=(AT-timedelta(hours=1)).isoformat(),expiry_utc=(AT+timedelta(days=13)).isoformat()))
        cfg=sender_config(); cfg['internal_domains']=['outreach.example.invalid']
        engine=Engine(sender,cfg,SECRET); self.store.wire_sender(engine)
        engine.receive(mail('Yes',address='buyer@example.invalid'),AT)
        job=sender.conn.execute('SELECT email_no FROM sends').fetchone()[0]
        self.pay(); smtp=FakeSMTP()
        self.assertEqual(engine.dispatch('p1',None,AT,smtp,service_job=job),'paid_service_cancelled')
        self.assertEqual(smtp.accepted,[])
        engine.receive(mail('refund',address='buyer@example.invalid'),AT)
        job=sender.conn.execute("SELECT email_no FROM sends WHERE template='ACK_REFUND'").fetchone()[0]
        self.assertEqual(engine.dispatch('p1',None,AT,smtp,service_job=job),'sent')


    def test_wrong_artifact_receipt_stays_unknown_and_cannot_mark_live(self):
        self.pay(); self.confirm(); self.store.promote('order-1')
        class WrongHost(FakeAdapter):
            def perform(self,key,kind,payload,at):
                result=super().perform(key,kind,payload,at)
                result['artifact_sha256']='wrong-artifact'
                return result
        host=WrongHost()
        self.assertIsNone(self.store.launch('order-1',AT+timedelta(hours=2),host))
        self.assertIsNone(self.store.launch('order-1',AT+timedelta(hours=3),host))
        self.assertIsNone(self.store.get('order-1')['live_at'])
        self.assertEqual(self.store.db.execute("SELECT state FROM effects WHERE kind='publish'").fetchone()[0],'unknown')
        self.assertEqual(len(host.calls),1)


class HttpTests(unittest.TestCase):
    pay=base.Flow.pay
    confirm=base.Flow.confirm
    def setUp(self):
        LifecycleTests.setUp(self); LifecycleTests.live(self)
        self.server=local_server(self.store,clock=lambda:AT+timedelta(hours=3))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
        self.addCleanup(self.stop)
        self.origin=self.server.allowed_origin; self.url=self.origin+'/enquiry/'+self.slug

    def stop(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()

    def form(self):
        with urlopen(self.url) as r: text=r.read().decode()
        return dict(re.findall(r'name="(id|timestamp|token)" value="([^"]+)"',text))

    def post(self,data,origin=None):
        request=Request(self.url,data=urlencode(data).encode(),headers={'Content-Type':'application/x-www-form-urlencoded','Origin':origin or self.origin})
        try:
            with urlopen(request) as r: return r.status
        except HTTPError as e:
            code=e.code; e.close(); return code

    def test_http_form_queues_once_and_blocks_cross_origin(self):
        fields={**self.form(),'name':'Visitor','email':'v@example.invalid','message':'Hello'}
        self.assertEqual(self.post(fields,origin='https://evil.example'),403)
        self.assertEqual(self.post(fields),202); self.assertEqual(self.post(fields),202)
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM enquiries').fetchone()[0],1)
        self.assertEqual(self.store.forward_enquiries(AT,FakeAdapter()),[fields['id']])

    def test_http_limits_token_expiry_schema_and_header_injection(self):
        fields={**self.form(),'name':'Visitor','email':'v@example.invalid','message':'Hello'}
        self.assertEqual(self.post({**fields,'token':'0'*64}),403)
        self.assertEqual(self.post({**fields,'timestamp':'0'}),400)
        self.assertEqual(self.post({**fields,'extra':'x'}),400)
        self.assertEqual(self.post({**fields,'name':'x\r\nBCC: attacker'}),400)
        for i in range(4): self.assertEqual(self.post(fields),202)
        self.assertEqual(self.post(fields),429)
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM enquiries').fetchone()[0],1)


class MailtoTests(unittest.TestCase):
    def test_exact_concept_mailto_in_both_checkout_states_without_form(self):
        spec=importlib.util.spec_from_file_location('sales_build',ROOT/'site/build.py')
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        config=json.loads((ROOT/'company/web-config.example.json').read_text())
        config.update(company='Example Company',postal_address='1 Test Lane',support_email='concepts@example.com',
                      public_base_url='https://www.example.com',checkout_base_url='https://checkout.example.com')
        expected="Don't have a concept yet? Email concepts@example.com with your business name and city and we'll build one"
        with tempfile.TemporaryDirectory() as root:
            for ready in (False,True):
                evidence={k:True for k in ('provider_eligible','commercial_host','checkout_signed_metadata','order_flow_verified')}
                evidence['checkout_status']=200
                out=Path(root)/str(ready); module.build(config,out,evidence if ready else {})
                page=(out/'index.html').read_text(encoding='utf-8')
                self.assertIn('href="mailto:concepts@example.com">'+expected+'</a>',page)
                self.assertNotIn('<form',page); self.assertNotIn('<script',page)
                self.assertEqual('Orders are not open yet' in page,not ready)
            config['support_email']='hello@example.com?bcc=another@example.com'
            with self.assertRaises(ValueError): module.build(config,Path(root)/'bad')
