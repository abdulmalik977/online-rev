"""REV-011 A8 fixtures, implemented within TASK-007's launch gate."""
from sender.tests.support import Fixture, AT
from sender.transports import FakeSMTP
from sender.rules import flags
from sender.gate import checks


class A8(Fixture):
    def test_21_stop_punctuation_is_optout(self):
        for text in ('Stop!', 'STOP.', ' \t\"Stop!\"; ', "'stop,'"):
            with self.subTest(text=text):
                self.assertIn('OPT_OUT', flags(text))
        result=self.receive('Stop!')
        self.assertTrue(self.store.suppressed('owner@plumber.invalid'))
        self.assertEqual(result['reply'],'ACK_UNSUB')
        for text in ('Yes!', 'ok.', ' "Sure;" '):
            self.assertIn('INTERESTED',flags(text))
        self.assertNotIn('OPT_OUT',flags('The stop is nearby.'))

    def test_22_sue_is_legal_accepted_false_positive(self):
        result=self.receive('Sue will call you')
        self.assertEqual(result['queue'],['legal'])
        self.assertIsNone(result['reply'])
        self.assertIn('LEGAL',flags('Sue will call you'))
        self.assertTrue(self.store.suppressed('owner@plumber.invalid'))
        self.assertEqual(len(self.sends()),0)
        rows=self.store.conn.execute('SELECT class FROM queue').fetchall()
        self.assertEqual([r['class'] for r in rows],['legal'])

    def test_23_mutated_config_refuses_dispatch(self):
        for bad in ('', '{POSTAL_ADDRESS}'):
            with self.subTest(postal_address=bad):
                self.config['postal_address']=bad
                smtp=FakeSMTP()
                self.assertEqual(self.engine.dispatch('p1',1,AT,smtp),'invalid_config')
                self.assertEqual(smtp.accepted,[])
                self.assertEqual(self.sends(),[])

    def test_service_reply_checks_current_config_too(self):
        self.receive('Yes!')
        job=self.sends()[0]['email_no']
        self.config['company']='{COMPANY}'
        smtp=FakeSMTP()
        self.assertEqual(self.engine.dispatch('p1',None,AT,smtp,service_job=job),'invalid_config')
        self.assertEqual(smtp.accepted,[])

    def test_config_edit_between_intent_and_transport_refused(self):
        from contextlib import contextmanager
        original=self.store.transaction
        count=0
        @contextmanager
        def edit_between_transactions():
            nonlocal count
            with original() as conn:
                yield conn
            count+=1
            if count==1:
                self.config['postal_address']=''
        self.store.transaction=edit_between_transactions
        smtp=FakeSMTP()
        self.assertEqual(self.engine.dispatch('p1',1,AT,smtp),'invalid_config')
        self.assertEqual(smtp.accepted,[])
        self.assertEqual(self.sends()[0]['status'],'failed')

    def test_gate_requires_each_a8_fixture(self):
        evidence={key:True for key in ('suppression_ready','role_filter','acceptance_20',
                  'extra_7','faq_8','no_unresolved_spec_tests','a8_21','a8_22','a8_23')}
        self.assertTrue(checks(self.config,evidence)[4][1])
        for key in ('a8_21','a8_22','a8_23'):
            with self.subTest(missing=key):
                incomplete=dict(evidence); incomplete.pop(key)
                self.assertFalse(checks(self.config,incomplete)[4][1])
