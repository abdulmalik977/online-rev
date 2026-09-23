"""Read-only launch checks; absent evidence is RED, never an inferred approval."""
from datetime import date
import ipaddress
import json
from pathlib import Path
import re
from .templates import safe_url


def validate(config):
    required={'company','postal_address','sending_domain','mailboxes','preview_base_url','unsub_base_url','checkout_base_url','target_regions','internal_domains','shared_mail_domains','us_federal_holidays','owner_queue_path','complaint_feed','analytics_exclude_ips'}
    if required-set(config):
        raise ValueError('Missing configuration: '+', '.join(sorted(required-set(config))))
    if config['target_regions']!=['Houston, TX'] or not config['company'].strip() or not config['postal_address'].strip():
        raise ValueError('Houston pilot and nonempty company/address required')
    if not 3<=len(config['mailboxes'])<=5 or len(set(config['mailboxes']))!=len(config['mailboxes']):
        raise ValueError('Three to five unique mailboxes required')
    if not re.fullmatch(r'[a-z0-9.-]+\.[a-z]{2,}',config['sending_domain']) or any(not re.fullmatch(r'[a-z0-9._-]+',m) for m in config['mailboxes']):
        raise ValueError('Invalid sending domain or mailbox')
    for key in ('preview_base_url','unsub_base_url','checkout_base_url'):
        safe_url(config[key])
    for day in config['us_federal_holidays']:
        date.fromisoformat(day)
    for cidr in config['analytics_exclude_ips']:
        ipaddress.ip_network(cidr)
    if re.search(r'\{[A-Za-z_][A-Za-z0-9_]*\}',json.dumps(config)):
        raise ValueError('Unresolved placeholder in configuration')
    return True


def checks(config=None,evidence=None):
    evidence=evidence or {}; config=config or {}
    try:
        valid=validate(config)
    except (ValueError,TypeError,KeyError):
        valid=False
    auth=evidence.get('mailboxes',[])
    passed=[m for m in auth if all(m.get(k) is True for k in ('spf','dkim','dmarc','external_test')) and m.get('dmarc_policy') in {'quarantine','reject'} and {'list-unsubscribe','list-unsubscribe-post'} <= set(m.get('dkim_signed_headers',[]))]
    return [
      ('1 SETUP-EMAIL and mailbox authentication',valid and len({m.get('local_part') for m in passed if m.get('local_part') in config.get('mailboxes',[])})>=3 and evidence.get('setup_email') is True),
      ('2 Complete Houston company configuration',valid),
      ('3 Commercial host, ten live previews, rehearsed and scheduled expiry',all(evidence.get(k) is True for k in ('commercial_host','ten_live_previews','remote_expiry_rehearsal','expiry_scheduled'))),
      ('4 Self-serve checkout 200 and enabled order button',evidence.get('checkout_status')==200 and evidence.get('order_button_enabled') is True),
      ('5 Suppression, role filter, 20+7 cases and FAQ',all(evidence.get(k) is True for k in ('suppression_ready','role_filter','acceptance_20','extra_7','faq_8','no_unresolved_spec_tests'))),
      ('6 External opt-out and signed one-click POST',all(evidence.get(k) is True for k in ('external_optout','direct_post','post_no_session','second_send_refused')) and len(passed)>=3),
      ('7 Legal escalation with zero outgoing mail',evidence.get('legal_escalation') is True),
      ('8 Pilot clock excludes tests and warm-up',evidence.get('pilot_clock_tested') is True),
      ('TASK-009 real sending disabled',False),
    ]


def load_optional(path):
    path=Path(path)
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
