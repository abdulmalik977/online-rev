"""A7 regression references: originally failing tests, now owner-approved behavior.

These exercise literal binding rules against their required operational outcomes.
The original proposals below were adopted verbatim in A7. Assertions are retained;
these tests must now pass as part of the complete suite, without skips or xfail.
"""
from datetime import timedelta
from sender.calendar import stamp,expiry
from sender.transports import FakeSMTP,FakeIMAP
from sender.tests.support import Fixture,AT,mail


class SpecConflicts(Fixture):
    def test_a4_absent_sent_copy_cannot_prove_non_delivery(self):
        """A7 prevents duplicate acceptance when an SMTP Sent copy is absent.

        Adopted proposal (A7): after 24h IMAP absence, keep unknown and require provider proof
        or owner reconciliation; only definite non-acceptance permits the retry.
        SMTP acceptance does not itself create a searchable IMAP Sent copy.
        """
        first=AT-timedelta(days=6)  # Thu Sep 17; email 2 is due Tue Sep 22.
        p=self.store.get('p1'); p['generated_at']=stamp(first); p['expiry_utc']=stamp(expiry(first)); self.store.save(p)
        self.engine.dispatch('p1',1,first,FakeSMTP())
        second=AT-timedelta(days=1)  # Tue Sep 22.
        smtp=FakeSMTP(['timeout_accepted'],sent_copy=False)
        self.assertEqual(self.engine.dispatch('p1',2,second,smtp),'unknown')
        self.engine.reconcile(AT,FakeIMAP(smtp.sent))  # A7 retains unknown despite the absent Sent copy.
        self.engine.dispatch('p1',2,AT,smtp)
        self.assertEqual(len(smtp.accepted),1,'A4 permits duplicate accepted email 2 after an absent Sent copy')

    def test_a6_owner_deadline_exists_for_non_customer(self):
        """A7 gives a non-buyer's legal queue a receipt-based deadline.

        Adopted proposal (A7): owner-response clock starts at inbound receipt; only launch and
        automatic-refund eligibility use later(payment, confirmation) in offer 4.
        """
        self.receive('My lawyer will contact you')
        row=self.store.conn.execute('SELECT due FROM queue').fetchone()
        self.assertIsNotNone(row['due'],'Non-paying legal request has no A6 owner-response start')

    def test_a6_short_body_digest_drops_a_distinct_optout(self):
        """A7 full-message identity preserves a distinct later opt-out.

        Adopted proposal (A7): hash the full canonical message (or stable provider UID plus
        mailbox identity), not a body prefix, when Message-ID is absent.
        """
        prefix='a'*600+'\n'
        self.engine.receive(mail(prefix+'Question',missing_id=True),AT,mailbox_id='hello')
        self.engine.receive(mail(prefix+'unsubscribe',missing_id=True),AT,mailbox_id='hello')
        self.assertTrue(self.store.suppressed('owner@plumber.invalid'),'Distinct opt-out was discarded as duplicate by A6 prefix hash')
