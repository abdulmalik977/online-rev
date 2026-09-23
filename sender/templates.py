"""Plain-text templates. Unknown placeholders and unsafe headers abort rendering."""
from email.message import EmailMessage
from hashlib import sha256
import re
from urllib.parse import urlparse, quote
from .rules import FAQ

SIGNATURE = 'The {COMPANY} team\n{COMPANY} · {POSTAL_ADDRESS}\n\nThis is a commercial email about website services. To stop receiving emails from us: {UNSUB_URL} (or reply with the word "unsubscribe"). We honor every request within 10 business days, usually the same day.'
OUTREACH = {
 1: "Hi {FIRST_NAME},\n\nWe build websites for plumbing and HVAC companies in {CITY}, and we made one for {BUSINESS} using the services listed on your current site:\n\n{PREVIEW_URL}\n\nIt's an independent concept, not your official site. If you'd like it, the order button is on the preview page: $119/month, no setup fee, cancel anytime. It goes live on a subdomain within two business days of your order and confirmation email, and on your own domain as soon as you point it there (we send the instructions).\n\nIf it's not for you, no reply needed. The preview is removed on {EXPIRY_DATE}.",
 2: "Hi {FIRST_NAME},\n\nFollowing up on the concept site we built for {BUSINESS}: {PREVIEW_URL}\n\nTwo things people ask: yes, it works on your existing domain, and yes, you can send us up to 5 change requests a month (each up to 30 minutes of work), done within two business days.\n\nThe preview is up until {EXPIRY_DATE}.",
 3: "Hi {FIRST_NAME},\n\nLast note from us: the concept site for {BUSINESS} comes down on {EXPIRY_DATE}.\n\n{PREVIEW_URL}\n\nIf you want it, the order button on that page is all it takes. If not, thanks for your time, and we won't email you again about this.",
}
REPLIES = {
 'ORDER': "Great — the order button is on your preview page: {PREVIEW_URL}. After you order and reply to the confirmation email, the site is live on a subdomain within two business days, and on your own domain as soon as you point it there (we send the DNS instructions). Anything you want changed, just email us.",
 'NO_CALL': "We work by email rather than calls — that's how we keep it at $119/month with no setup fee. Ask anything here and we'll answer within one business day.",
 'ACK_QUESTION': "Thanks — good question. We'll come back to you by the next business day.",
 'ACK_NOT_NOW': "No problem — we'll leave it there. Thanks for the reply.",
 'ACK_NEGATIVE': "Understood, thanks for letting us know. You're removed from our list.",
 'ACK_UNSUB': "Done — you're unsubscribed and won't hear from us again.",
 'ACK_REFUND': "Received — a person will come back to you within one business day.",
}
REPLIES['NO_CALL_ORDER']=REPLIES['NO_CALL']+" When you're ready, the order button is on the preview page: {PREVIEW_URL}."
SUBJECTS=['A new website for {BUSINESS} (preview inside)','{BUSINESS} — we built you a website concept','Quick one: your {CITY} plumbing site, redesigned']


def stable_index(value, size):
    return int(sha256(value.encode()).hexdigest()[:8],16)%size


def safe_url(value):
    p=urlparse(value)
    if p.scheme!='https' or not p.hostname or p.username or p.password or any(c in value for c in '\r\n'):
        raise ValueError('HTTPS URL without credentials required')
    return value.rstrip('/')


def variables(config, p, token):
    return dict(COMPANY=config['company'],POSTAL_ADDRESS=config['postal_address'],
                FIRST_NAME=p.get('first_name') or 'there',BUSINESS=p['business'],CITY=p['city'],
                PREVIEW_URL=safe_url(config['preview_base_url'])+'/'+quote(p['preview_slug'],safe='')+'/',
                EXPIRY_DATE=p['expiry_utc'],UNSUB_URL=safe_url(config['unsub_base_url'])+'/'+token)


def fill(template, values):
    try:
        result=template.format_map(values)
    except (KeyError,ValueError) as e:
        raise ValueError('Unresolved template field') from e
    if re.search(r'\{[^{}]+\}',result):
        raise ValueError('Unresolved placeholder in output')
    return result


def render(config, p, token, message_id, number=None, reply=None, faq=(), owner_text=None):
    values=variables(config,p,token)
    footer=fill(SIGNATURE,values)
    if number:
        body=fill(OUTREACH[number],values)+'\n\n'+footer
    elif owner_text is not None:
        body=fill(owner_text,values)+'\n\n'+footer
    else:
        template='Thanks for asking.\n\n'+'\n\n'.join(FAQ[k][1] for k in faq) if reply=='FAQ_REPLY' else REPLIES[reply]
        body=fill(template,values)+'\n\n'+(fill('{COMPANY} · {POSTAL_ADDRESS}',values) if reply=='ACK_UNSUB' else footer)
    subject=fill(SUBJECTS[p.get('subject_variant',stable_index(p['id'],3))],values)
    mailbox=p['mailbox']+'@'+config['sending_domain']
    for field in (mailbox,p['email'],config['company'],subject,message_id,p.get('thread_message_id','')):
        if any(c in field for c in '\r\n'):
            raise ValueError('Header injection refused')
    msg=EmailMessage()
    msg['From']=f"{config['company']} <{mailbox}>"; msg['Reply-To']=mailbox
    msg['To']=p['email']; msg['Message-ID']=message_id
    msg['Subject']=subject if number==1 else 'Re: '+subject
    if number!=1 and p.get('thread_message_id'):
        msg['In-Reply-To']=p['thread_message_id']; msg['References']=p['thread_message_id']
    if number:
        msg['List-Unsubscribe']=f"<{values['UNSUB_URL']}>, <mailto:{mailbox}?subject=unsubscribe>"
        msg['List-Unsubscribe-Post']='List-Unsubscribe=One-Click'
    else:
        msg['Auto-Submitted']='auto-replied'
    msg.set_content(body)
    return msg
