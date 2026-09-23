"""Reproducible synthetic order demonstration. Everything stays in the chosen local root."""
import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from generator.build import build, FIELDS
from .config import PLAN, AMOUNT
from .flow import Orders, signature


def demo(root):
    root=Path(root)
    if root.exists():
        raise ValueError('Choose a new demo directory')
    root.mkdir(parents=True)
    at=datetime.now(timezone.utc).replace(microsecond=0)
    row=dict(business='Fixture Plumbing',city='Houston',state='TX',category='plumbing',
             website='https://plumbing.example.invalid',phone='+15555550100',services='Plumbing repairs|Water heaters',
             source_url='https://plumbing.example.invalid',checked_on=at.date().isoformat(),maps_url='',maps_status='pending')
    with (root/'fixture.csv').open('w',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=FIELDS); writer.writeheader(); writer.writerow(row)
    build(root/'fixture.csv',root/'preview',at.date(),at.date())
    slug=json.loads((root/'preview/records.json').read_text())[0]['slug']
    secret=b'synthetic-demo-secret-not-for-production'
    store=Orders(root/'private',secret,{})
    try:
        store.register_preview(root/'preview',slug,'buyer@example.invalid',at)
        payload=json.dumps(dict(event_id='fake-event-1',type='order.paid',order_id='fake-order-1',email='buyer@example.invalid',
                                preview_slug=slug,plan=PLAN,amount_minor=AMOUNT,currency='USD',paid_at=at.isoformat())).encode()
        ts=int(at.timestamp()); store.accept(payload,ts,signature(payload,secret,ts),at)
        store.confirm('fake-order-1','buyer@example.invalid',at,domain='subdomain',corrections='',media_consent=False,verified=True)
        customer=store.promote('fake-order-1')
        result={'synthetic':True,'payments_taken':0,'messages_sent':0,'deployed':False,
                'preview':str((root/'preview/previews'/slug/'index.html').resolve()),
                'customer':str(customer/'index.html'),'order_status':store.get('fake-order-1')['status']}
        (root/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        return result
    finally:
        store.close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',required=True)
    print(json.dumps(demo(p.parse_args().output),indent=2))
