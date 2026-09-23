"""Build only public sales assets; default output has checkout disabled."""
import argparse
from html import escape
import json
import re
from urllib.parse import quote
from pathlib import Path
from string import Template
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from orders.config import load, checkout_ready, text

HERE=Path(__file__).resolve().parent


def build(config,output,evidence=None):
    evidence=evidence or {}
    ready=checkout_ready(config,evidence)
    output=Path(output)
    if output.exists():
        raise ValueError('Choose a new output directory')
    company=escape(config.get('company') or '[Company name]')
    address=escape(config.get('postal_address') or '[Postal address]')
    support=config.get('support_email','')
    if not isinstance(support,str) or not re.fullmatch(r'[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',support):
        raise ValueError('A valid support_email is required for the concept mailto link')
    concept_request=(f'<p class="concept-request"><a href="mailto:{quote(support,safe=chr(64))}">'
                     f"Don't have a concept yet? Email {escape(support)} with your business name and city and we'll build one</a></p>")
    support_link=(f'<a href="mailto:{escape(support,quote=True)}">Email {escape(support)}</a>'
                  if text(support) and '@' in support and not support.endswith('.invalid')
                  else 'Contact details will be available when orders open.')
    checkout=(f'<a class="button" href="{escape(config["checkout_base_url"],quote=True)}" rel="noreferrer">Choose your preview and subscribe ↗</a>'
              if ready else '<button class="button" type="button" disabled>Orders are not open yet</button>')
    page=Template((HERE/'template.html').read_text(encoding='utf-8')).substitute(
        company=company,postal_address=address,support_link=support_link,checkout=checkout,concept_request=concept_request,
        checkout_note=('Use the order link on your preview to keep your design linked to your subscription.' if ready
                       else 'You can explore the service here. Subscriptions will open once setup is complete.'),
        robots='' if ready else '<meta name="robots" content="noindex,nofollow">')
    def document(title,body):
        return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self'; script-src 'none'; connect-src 'none'; form-action 'none'; base-uri 'none'"><title>{title} | {company}</title><link rel="stylesheet" href="style.css"></head><body><header class="wrap nav"><a class="brand" href="./">{company}</a><a href="./">Back to the service</a></header><main class="wrap legal-page"><h1>{title}</h1>{body}</main><footer class="footer"><div class="wrap"><p>{company}<br>{address}</p><a href="privacy.html">Privacy</a></div></footer></body></html>'''
    privacy=document('Privacy',f'''<p>This page describes the information used to provide our website service. Orders are not processed on this page.</p><h2>Information you give us</h2><p>When you subscribe, we use your contact details, chosen preview, payment confirmation and the business content you approve to build and maintain your site. Your payment provider handles card details; we do not receive full card numbers.</p><h2>Website visits and enquiries</h2><p>This sales page sets no cookies and has no analytics script. Customer sites are intended to report aggregate visits and form submissions using cookie-free analytics. Enquiry forms send the details you enter to the business you contact; do not submit sensitive information.</p><h2>Service providers and records</h2><p>Hosting, payment and email providers process the information needed for their services. Records are used to fulfil orders, support customers, resolve disputes and meet applicable recordkeeping requirements. Provider details will be confirmed before subscriptions open.</p><h2>Your choices</h2><p>Use the unsubscribe link in an outreach email to stop further outreach. Service messages about an existing order are separate. You can contact us about access, corrections or deletion of your information. {support_link}</p>''')
    unsub=document('Email preferences','<p>To stop outreach emails, open the unsubscribe link in the email you received. It identifies your subscription without asking you to enter an email address.</p><p>The link opens a confirmation button. Visiting the link alone does not unsubscribe you. Submitting the button stops future outreach.</p><p>No mailing-list change has been made by visiting this page.</p>')
    output.mkdir(parents=True)
    for name,body in (('index.html',page),('privacy.html',privacy),('unsubscribe.html',unsub)):
        (output/name).write_text(body,encoding='utf-8',newline='\n')
    (output/'style.css').write_bytes((HERE/'style.css').read_bytes())
    (output/'_headers').write_text("/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: no-referrer\n  Cache-Control: no-cache\n  X-Frame-Options: DENY\n",encoding='utf-8')
    return {'checkout_enabled':bool(ready),'files':sorted(p.name for p in output.iterdir()),
            'bytes':sum(p.stat().st_size for p in output.iterdir())}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='company/web-config.example.json')
    parser.add_argument('--evidence')
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    print(json.dumps(build(load(args.config),args.output,load(args.evidence) if args.evidence else {}),indent=2))
