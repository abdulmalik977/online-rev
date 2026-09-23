from datetime import datetime, timedelta, timezone, date
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from generator.build import build
from orders.config import PLAN, AMOUNT
from orders.flow import Orders, signature, business_deadline
from orders.launch_gate import launch_checks

ROOT=Path(__file__).resolve().parents[2]
AT=datetime(2026,9,23,14,tzinfo=timezone.utc)
SECRET=b'test-secret-never-use-in-production-000'


class Flow(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.bundle=self.root/'previews'
        build(ROOT/'generator/testset.csv',self.bundle,date(2026,9,22),date(2026,9,23))
        self.slug=json.loads((self.bundle/'records.json').read_text(encoding='utf-8'))[0]['slug']
        self.store=Orders(self.root/'private',SECRET,{})
        self.addCleanup(self.store.close)
        self.store.register_preview(self.bundle,self.slug,'buyer@example.invalid',AT)
        self.event=dict(event_id='evt-1',type='order.paid',order_id='order-1',email='buyer@example.invalid',preview_slug=self.slug,
                        plan=PLAN,amount_minor=AMOUNT,currency='USD',paid_at=AT.isoformat())

    def pay(self,event=None,at=AT):
        raw=json.dumps(event or self.event).encode(); timestamp=int(at.timestamp())
        return self.store.accept(raw,timestamp,signature(raw,SECRET,timestamp),at)

    def confirm(self,**kw):
        options=dict(domain='subdomain',corrections='',media_consent=False,verified=True)
        options.update(kw)
        return self.store.confirm('order-1','buyer@example.invalid',AT+timedelta(hours=1),**options)

    def test_signed_payment_confirmation_promotes_end_to_end(self):
        row=self.pay(); self.assertEqual(row['status'],'awaiting_confirmation')
        self.assertIsNone(row['launch_due'])
        self.assertTrue((self.root/'private/welcome/order-1.txt').is_file())
        with self.assertRaises(ValueError): self.store.promote('order-1')
        row=self.confirm(); self.assertEqual(row['launch_due'],'2026-09-25T15:00:00+00:00')
        folder=self.store.promote('order-1')
        html=(folder/'index.html').read_text(encoding='utf-8')
        for token in ('noindex','preview-bar','expiry.js','data-expires','INDEPENDENT CONCEPT','FOR THE BUSINESS OWNER'):
            self.assertNotIn(token,html)
        self.assertIn('Services for your home.',html)
        self.assertEqual({p.name for p in folder.iterdir()},{'index.html','privacy.html','house.svg','style.css','_headers'})
        self.assertIn('prepared',(self.root/'private/orders.md').read_text())
        self.assertIsNone(self.store.get('order-1')['live_at'])
        self.assertEqual(self.store.promote('order-1'),folder)
        # Original preview retains its original labels and expiry.
        self.assertIn('noindex',(self.bundle/'previews'/self.slug/'index.html').read_text(encoding='utf-8'))

    def test_invalid_signature_replay_window_and_amount_never_create_order(self):
        raw=json.dumps(self.event).encode(); timestamp=int(AT.timestamp())
        with self.assertRaises(ValueError): self.store.accept(raw,timestamp,'0'*64,AT)
        with self.assertRaises(ValueError): self.store.accept(raw,timestamp,signature(raw,SECRET,timestamp),AT+timedelta(minutes=6))
        for patch in ({'amount_minor':100},{'currency':'EUR'},{'type':'order.refunded'},{'plan':'another'},{'email':'stranger@example.invalid'},{'preview_slug':'../../secrets'},{'paid_at':(AT+timedelta(days=1)).isoformat()}):
            with self.subTest(patch=patch):
                with self.assertRaises(ValueError): self.pay({**self.event,**patch})
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM orders').fetchone()[0],0)

    def test_idempotency_event_and_order_conflicts(self):
        self.pay(); self.pay()
        self.pay({**self.event,'event_id':'evt-2'})
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM orders').fetchone()[0],1)
        with self.assertRaises(ValueError): self.pay({**self.event,'email':'wrong@example.invalid'})
        with self.assertRaises(ValueError): self.pay({**self.event,'event_id':'evt-3','paid_at':(AT-timedelta(seconds=1)).isoformat()})
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM events').fetchone()[0],2)

    def test_duplicate_payment_queues_refund_and_returns_existing_order(self):
        original=self.pay()
        duplicate={**self.event,'event_id':'evt-2','order_id':'order-2'}
        self.assertEqual(self.pay(duplicate),original)
        for event in (duplicate,{**duplicate,'event_id':'evt-3'}):
            self.assertEqual(self.pay(event),original)
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM orders').fetchone()[0],1)
        queue=self.store.db.execute('SELECT class,order_id,original_order_id FROM owner_queue').fetchall()
        self.assertEqual([tuple(row) for row in queue],[('refund','order-2','order-1')])
        audit=self.store.db.execute("SELECT order_id FROM audit WHERE action='duplicate_payment'").fetchall()
        self.assertEqual([row[0] for row in audit],['order-2'])
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM events').fetchone()[0],3)
        report=(self.root/'private/orders.md').read_text(encoding='utf-8')
        self.assertIn('class refund | duplicate order-2 | original order-1',report)
        self.assertEqual(len(list((self.root/'private/welcome').glob('*.txt'))),1)

    def test_expired_payment_and_registration_refused(self):
        late=AT+timedelta(days=15)
        with self.assertRaises(ValueError): self.pay({**self.event,'paid_at':late.isoformat()},late)
        with self.assertRaises(ValueError): self.store.register_preview(self.bundle,self.slug,'buyer@example.invalid',late)

    def test_confirmation_authentication_and_corrections_hold(self):
        self.pay()
        with self.assertRaises(PermissionError): self.confirm(verified=False)
        with self.assertRaises(ValueError):
            self.store.confirm('order-1','stranger@example.invalid',AT,domain='subdomain',corrections='',media_consent=False,verified=True)
        self.assertEqual(self.confirm(corrections='Please fix phone')['status'],'needs_corrections')
        with self.assertRaises(ValueError): self.store.promote('order-1')

    def test_confirmation_is_idempotent_and_does_not_reset_clock(self):
        self.pay(); first=self.confirm()
        later=self.store.confirm('order-1','buyer@example.invalid',AT+timedelta(days=3),domain='subdomain',corrections='',media_consent=False,verified=True)
        self.assertEqual(first['launch_due'],later['launch_due'])
        with self.assertRaises(ValueError): self.confirm(domain='other.example')

    def test_refund_clock_requires_confirmation_and_hosted_launch(self):
        self.pay(); self.assertEqual(self.store.refund_candidates(AT+timedelta(days=30)),[])
        row=self.confirm(); self.store.promote('order-1')
        deadline=datetime.fromisoformat(row['refund_due'])
        self.assertEqual(self.store.refund_candidates(deadline-timedelta(seconds=1)),[])
        self.assertEqual(len(self.store.refund_candidates(deadline)),1)
        self.assertEqual(self.store.get('order-1')['status'],'prepared')

    def test_calendar_business_days_holiday_dst_and_later_payment(self):
        start=datetime(2026,10,30,13,tzinfo=timezone.utc)
        self.assertEqual(business_deadline(start,2,['2026-11-02']),'2026-11-04T14:00:00+00:00')
        self.pay()
        row=self.store.confirm('order-1','buyer@example.invalid',AT-timedelta(hours=2),domain='subdomain',corrections='',media_consent=False,verified=True)
        self.assertEqual(row['launch_due'],'2026-09-25T14:00:00+00:00')

    def test_form_is_disabled_until_delivery_verified_and_private_outbox_dedups(self):
        self.pay(); self.confirm(); folder=self.store.promote('order-1')
        self.assertNotIn('<form ',(folder/'index.html').read_text(encoding='utf-8'))
        value=self.store.enquiry('request-1',self.slug,AT,name='Homeowner',email='home@example.invalid',message='Water heater question')
        self.assertFalse(value['delivered'])
        self.store.enquiry('request-1',self.slug,AT,name='Homeowner',email='home@example.invalid',message='Water heater question')
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM enquiries').fetchone()[0],1)
        with self.assertRaises(ValueError): self.store.enquiry('request-1',self.slug,AT,name='Different',email='home@example.invalid',message='Changed')

    def test_existing_modified_customer_artifact_is_not_overwritten(self):
        self.pay(); self.confirm(); folder=self.store.promote('order-1')
        (folder/'index.html').write_text('Owner edited this',encoding='utf-8')
        with self.assertRaises(ValueError): self.store.promote('order-1')
        self.assertEqual((folder/'index.html').read_text(),'Owner edited this')


class SalesPage(unittest.TestCase):
    def test_public_bundle_excludes_private_config_and_disables_checkout(self):
        spec=importlib.util.spec_from_file_location('sales_build',ROOT/'site/build.py')
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as root:
            config=json.loads((ROOT/'company/web-config.example.json').read_text())
            config['webhook_secret']='private-secret-never-render'
            out=Path(root)/'public'; result=module.build(config,out)
            self.assertFalse(result['checkout_enabled'])
            self.assertLess(result['bytes'],50000)
            html=(out/'index.html').read_text(encoding='utf-8')
            self.assertIn('disabled>Orders are not open yet',html)
            self.assertIn('$119',html); self.assertIn('5 business days',html)
            for p in out.iterdir(): self.assertNotIn('private-secret-never-render',p.read_text(encoding='utf-8'))
            self.assertEqual(result['files'],['_headers','index.html','privacy.html','style.css','unsubscribe.html'])

    def test_gate_cannot_override_failed_a8_with_supplied_evidence(self):
        values=launch_checks({},dict(a8_21=True,a8_22=True,a8_23=True),dict(a8_21=False,a8_22=True,a8_23=True))
        self.assertFalse(dict(values)['A8 fixture 21 Stop! is OPT_OUT'])
        self.assertFalse(all(ok for _,ok in values))
