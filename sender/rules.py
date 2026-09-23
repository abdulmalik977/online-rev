"""Pure email parsing and DEC-008 A1/A2/A5 decisions; no I/O."""
from dataclasses import dataclass, field
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
from hashlib import sha256
from html.parser import HTMLParser
import json
import re

TERMINAL = {'suppressed', 'paid', 'expired'}
SHARED = set('gmail.com googlemail.com yahoo.com ymail.com outlook.com hotmail.com live.com msn.com icloud.com me.com mac.com aol.com comcast.net att.net sbcglobal.net verizon.net protonmail.com proton.me mail.com'.split())
ROLES = set('abuse postmaster noreply no-reply donotreply legal privacy security mailer-daemon hostmaster webmaster'.split())
WORDS = {
 'OPT_OUT': ['unsubscribe','opt out','opt-out','take me off','remove me','stop emailing','stop sending','no more emails','do not contact',"don't contact","don't email"],
 'LEGAL': ['lawyer','attorney','legal action','cease and desist','sue','lawsuit','ftc','report you','spam complaint','harassment'],
 'REFUND': ['refund','money back','chargeback','charge back','dispute the charge'],
 'NOT_NOW': ['not now','not right now','not at the moment','not for now','maybe later','later this year','next month','next year','next quarter','check back','circle back','busy right now','in a few months'],
 'NEGATIVE': ['not interested','no thanks','no thank you',"we're good",'we are good','already have',"don't need",'do not need','pass'],
 'INTERESTED': ['interested',"let's do it",'lets do it','sign me up','sign up','how do i order','how do i sign up',"i'll take it",'i want it','go ahead','sounds good',"let's go"],
 'CALL': ['call me','give me a call','phone call','schedule a call','hop on a call','talk on the phone'],
}
TEMPORAL = ['right now','at the moment','for now','at this time','currently','this year','later','maybe']
FAQ = {
 'domain': (['domain','url','my site','existing site','dns'], 'Yes, it runs on your existing domain. After you order we send a one-page instruction for your DNS provider; until then the site is live on a subdomain of ours.'),
 'changes': (['change','changes','edit','update','updates','add a','remove'], 'Email us the change. Up to 5 requests a month are included (each up to 30 minutes of work), done within two business days.'),
 'contract': (['contract','cancel','cancellation','commitment','lock in','lock-in','month to month','month-to-month'], 'Month to month. Cancel anytime from your receipt email; the site stays up to the end of the paid month and you get a zip export.'),
 'photos': (['photo','photos','pictures','images','logo'], "Send us your own photos or logo and we'll swap them in. We only use images you own or have permission to use."),
 'hosting': (['hosting','host','ssl','https','secure'], 'Hosting and HTTPS are included.'),
 'timing': (['how long','how fast','when','turnaround','days'], "Live on a subdomain within two business days of your order and confirmation email. If it isn't live within 5 business days, the first month is refunded automatically."),
 'price': (['price','cost','how much','fee','setup'], '$119/month, no setup fee, cancel anytime. The order button is on your preview page.'),
 'who': (['who are you','who is this','your company','legit','scam'], "We're {COMPANY}, a small team that builds and maintains websites for trade businesses. We work by email; our postal address is in every message we send."),
}


def normalize(address):
    address = parseaddr(address)[1].lower().strip().strip('<>')
    if address.count('@') != 1 or any(c.isspace() for c in address):
        raise ValueError('Invalid mailbox address')
    local, domain = address.rsplit('@', 1)
    if not local or not domain:
        raise ValueError('Invalid mailbox address')
    return local + '@' + domain.encode('idna').decode('ascii')


def matches(body, words):
    return [m for word in words for m in re.finditer(r'\b' + re.escape(word) + r'\b', body)]


def flags(body):
    body = ' '.join(body.lower().split())
    found = {name for name in ('OPT_OUT','LEGAL','REFUND') if matches(body, WORDS[name])}
    if body.strip(" .,!?;:\"'") == 'stop':
        found.add('OPT_OUT')
    spans = []
    for name in ('NEGATIVE','NOT_NOW'):
        hits = matches(body, WORDS[name])
        if hits:
            found.add(name)
            spans.extend((m.start(), m.end()) for m in hits)
    reduced = ''.join(' ' if any(a <= i < b for a, b in spans) else c for i, c in enumerate(body))
    reduced = ' '.join(reduced.split())
    if 'NEGATIVE' in found and matches(body, TEMPORAL):
        found.remove('NEGATIVE')
        found.add('NOT_NOW')
    for name in ('INTERESTED','CALL'):
        if matches(reduced, WORDS[name]):
            found.add(name)
    if reduced.strip(" .,!?;:\"'") in {'yes','yes please','ok','okay','sure'}:
        found.add('INTERESTED')
    if '?' in reduced:
        found.add('QUESTION')
    return found


def faq_matches(body):
    order = []
    for index, (key, (keywords, _)) in enumerate(FAQ.items()):
        hits = matches(body.lower(), keywords)
        if hits:
            order.append((min(m.start() for m in hits), index, key))
    return [entry[2] for entry in sorted(order)[:2]]


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in {'p','div','br','blockquote','li'}:
            self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in {'p','div','blockquote','li'}:
            self.parts.append('\n')
    def handle_data(self, data):
        self.parts.append(data)


def parse(raw, signature='', *, mailbox_id=None, provider_uid=None):
    message = BytesParser(policy=policy.default).parsebytes(raw)
    part = message.get_body(preferencelist=('plain','html')) if message.is_multipart() else message
    text = part.get_content() if part and part.get_content_maintype() == 'text' else ''
    if part and part.get_content_subtype() == 'html':
        parser = Text(); parser.feed(text); text = ''.join(parser.parts)
    origin = message.get('Auto-Submitted')
    auto = (origin is not None and origin.split(';')[0].strip().lower() != 'no') or any(h in message for h in ('X-Autoreply','X-Autorespond')) or str(message.get('Precedence','')).lower() == 'auto_reply'
    no_reply = 'X-Auto-Response-Suppress' in message or str(message.get('Precedence','')).lower() in {'bulk','junk'}
    lines = []
    for line in text.replace('\r\n','\n').splitlines():
        if re.match(r'^(On .+ wrote:|From: .+|-----Original Message-----|_{5,})$', line) or line == '-- ':
            break
        if not line.startswith('>'):
            lines.append(line)
    body = '\n'.join(lines)
    if signature:
        body = body.replace(signature, '')
    body = ' '.join(body.lower().split())
    ident = str(message.get('Message-ID','')).strip()
    if not ident:
        if not isinstance(mailbox_id,str) or not mailbox_id.strip():
            raise ValueError('Receiving mailbox identity is required without Message-ID')
        # A7: preserve every header, MIME part and body byte except line endings.
        # JSON frames the receiver/UID fields; UID should include UIDVALIDITY.
        metadata=json.dumps([mailbox_id, str(provider_uid) if provider_uid is not None else None],
                            ensure_ascii=True,separators=(',',':')).encode('ascii')
        canonical=raw.replace(b'\r\n',b'\n').replace(b'\r',b'\n')
        ident = 'sha256:' + sha256(metadata+b'\0'+canonical).hexdigest()
    recipients, original_ids = [], []
    is_dsn = message.get_content_type() == 'multipart/report' and message.get_param('report-type') == 'delivery-status'
    if is_dsn:
        for node in message.walk():
            if node.get_content_type() == 'message/delivery-status':
                for block in node.get_payload():
                    address = block.get('Original-Recipient') or block.get('Final-Recipient')
                    status = str(block.get('Status',''))
                    if address and re.fullmatch(r'[45]\.\d+\.\d+', status):
                        recipients.append((normalize(str(address).split(';')[-1].strip()), status))
            if node.get('Message-ID') and node is not message:
                original_ids.append(str(node['Message-ID']))
    return dict(id=ident, sender=normalize(str(message.get('From',''))), body=body, flags=flags(body),
                auto=bool(auto), no_reply=no_reply, dsn=is_dsn, recipients=recipients,
                references=re.findall(r'<[^>]+>', str(message.get('References','')) + ' ' + str(message.get('In-Reply-To',''))) + original_ids)


@dataclass
class Decision:
    state: str
    suppression: list = field(default_factory=list)
    queue: list = field(default_factory=list)
    reply: str | None = None
    faq: list = field(default_factory=list)
    kind: str = 'human'


def decide(event, state='active', reply_count=0):
    d = Decision(state)
    f = event['flags']
    def change(value):
        if d.state not in TERMINAL:
            d.state = value
    if event['auto']:
        d.kind = 'auto'
        return d
    if 'OPT_OUT' in f:
        d.suppression.append('unsubscribe'); change('suppressed')
        if 'LEGAL' in f:
            d.suppression.append('legal'); d.queue.append('legal')
        elif 'REFUND' in f:
            d.queue.append('refund'); d.reply = 'ACK_REFUND'
        else:
            d.reply = 'ACK_UNSUB'
    elif 'LEGAL' in f:
        d.suppression.append('legal'); change('suppressed'); d.queue.append('legal')
    elif 'REFUND' in f:
        d.queue.append('refund'); d.reply = 'ACK_REFUND'
    elif 'INTERESTED' in f and f & {'NEGATIVE','NOT_NOW'}:
        d.queue.append('uncertain')
    elif 'NOT_NOW' in f:
        change('not_now'); d.reply = 'ACK_NOT_NOW'
    elif 'NEGATIVE' in f:
        d.suppression.append('negative'); change('suppressed'); d.reply = 'ACK_NEGATIVE'
    elif 'CALL' in f:
        d.reply = 'NO_CALL_ORDER' if 'INTERESTED' in f else 'NO_CALL'
    elif 'INTERESTED' in f:
        d.reply = 'ORDER'
    elif 'QUESTION' in f:
        d.faq = faq_matches(event['body'])
        d.reply = 'FAQ_REPLY' if d.faq else 'ACK_QUESTION'
        if not d.faq:
            d.queue.append('question')
    else:
        d.queue.append('other')
    if d.state == 'active':
        change('replied')
    if d.reply and (event['no_reply'] or (reply_count >= 2 and d.reply not in {'ACK_UNSUB','ACK_REFUND'})):
        d.queue.append('reply_suppressed' if event['no_reply'] else 'reply_ceiling')
        d.reply = None
    return d
