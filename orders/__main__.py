"""Operate private local order files. No network, email or payment execution."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from .config import load
from .flow import Orders


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',required=True,help='Private runtime directory; never public site output')
    p.add_argument('--config',default='company/web-config.example.json')
    p.add_argument('--secret-env',default='ORDER_WEBHOOK_SECRET')
    commands=p.add_subparsers(dest='command',required=True)
    reg=commands.add_parser('register'); reg.add_argument('--bundle',required=True); reg.add_argument('--slug',required=True); reg.add_argument('--email',required=True)
    pay=commands.add_parser('payment'); pay.add_argument('--payload',required=True); pay.add_argument('--headers',required=True,help='Private JSON: timestamp integer, signature hex')
    promote=commands.add_parser('promote'); promote.add_argument('--order',required=True)
    commands.add_parser('project'); commands.add_parser('refund-candidates')
    args=p.parse_args(); secret=os.environ.get(args.secret_env,'').encode()
    if len(secret)<32:
        p.error('Set the private secret environment variable to at least 32 bytes; do not commit it')
    store=Orders(args.root,secret,load(args.config)); at=datetime.now(timezone.utc)
    try:
        if args.command=='register':
            store.register_preview(args.bundle,args.slug,args.email,at); result={'registered':args.slug}
        elif args.command=='payment':
            headers=load(args.headers)
            row=store.accept(Path(args.payload).read_bytes(),headers['timestamp'],headers['signature'],at)
            result={'order':row['id'],'status':row['status']}
        elif args.command=='promote':
            result={'local_artifact':str(store.promote(args.order)),'deployed':False}
        elif args.command=='project':
            store.project(); result={'projection':'orders.md and welcome/ in private runtime root'}
        else:
            result={'eligible_orders':[r['id'] for r in store.refund_candidates(at)],'refunds_executed':0}
        print(json.dumps(result,indent=2))
    finally:
        store.close()


if __name__=='__main__':
    main()
