"""Execute A8 locally, then print the inherited and order-flow launch gates."""
import argparse
import io
import json
import unittest
from sender.gate import checks
from sender.tests.test_a8 import A8
from .config import load, checkout_ready


def local_a8():
    result=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(A8))
    ok=result.wasSuccessful() and result.testsRun==6 and not result.skipped
    return {key:ok for key in ('a8_21','a8_22','a8_23')}


def launch_checks(config,evidence,a8):
    evidence=dict(evidence)
    # Supplied evidence cannot overwrite this invocation's actual fixture result.
    evidence.update(a8)
    return checks(config,evidence)+[
        ('A8 fixture 21 Stop! is OPT_OUT',a8.get('a8_21') is True),
        ('A8 fixture 22 Sue will call you is LEGAL',a8.get('a8_22') is True),
        ('A8 fixture 23 config edit prevents SMTP acceptance',a8.get('a8_23') is True),
        ('TASK-007 complete identity and provider checkout',bool(checkout_ready(config,evidence))),
        ('TASK-007 signed real provider adapter',evidence.get('provider_webhook_verified') is True),
        ('TASK-007 hosted landing page and mobile performance',all(evidence.get(k) is True for k in ('landing_https','mobile_under_1s','lighthouse_90'))),
        ('TASK-007 form delivery and abuse controls',all(evidence.get(k) is True for k in ('form_delivery_verified','form_abuse_controls'))),
        ('TASK-007 welcome, cancellation, refund execution and weekly export',all(evidence.get(k) is True for k in ('welcome_delivery','cancellation_verified','refund_execution','weekly_export_30_days'))),
        ('TASK-007 independent Claude PASS',evidence.get('task007_review_pass') is True),
    ]


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='company/web-config.example.json')
    parser.add_argument('--evidence')
    args=parser.parse_args()
    values=launch_checks(load(args.config),load(args.evidence) if args.evidence else {},local_a8())
    for title,ok in values:
        print(('GREEN ' if ok else 'RED ')+title)
    raise SystemExit(0 if all(ok for _,ok in values) else 2)
