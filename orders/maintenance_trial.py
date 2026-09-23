"""Timed bounded trial on synthetic data; not a production labor-savings claim."""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import time
from .demo import demo
from .flow import Orders
from .lifecycle import FakeAdapter


def trial():
    cases=[
        ('confirmed hours',{'hours':'Mon-Fri 8am-5pm'}),
        ('corrected phone',{'phone':'+15555550199'}),
        ('confirmed intro',{'intro':'Plumbing repairs for Houston homes.'}),
        ('confirmed service add',{'services':['Plumbing repairs','Water heaters','Drain cleaning']}),
        ('confirmed service removal',{'services':['Plumbing repairs']}),
        ('customer price text',{'prices':'Diagnostic visit: $99, as confirmed by the business.'}),
        ('customer headline',{'headline':'Plumbing help close to home.'}),
        ('unstructured correction',{'freeform':'Make it more premium; not sure how.'}),
        ('unsupported photo format',{'photo':{'path':'customer.jpg','consent':True,'alt':'Customer photo'}}),
        ('missing media permission',{'photo':{'path':'customer.png','consent':False,'alt':'Photo'}}),
    ]
    results=[]
    for i,(label,patch) in enumerate(cases):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'trial'; demo(root)
            store=Orders(root/'private',b'synthetic-demo-secret-not-for-production',{})
            try:
                at=datetime.now(timezone.utc)+timedelta(seconds=1)
                store.launch('fake-order-1',at,FakeAdapter())
                (store.root/'customer.jpg').write_bytes(b'jpeg not supported by this bounded automation')
                start=time.perf_counter(); outcome='manual_review'
                try:
                    store.apply_change('fake-order-1','trial-'+str(i),patch,at+timedelta(seconds=1),verified=True)
                    store.promote('fake-order-1')
                    store.launch('fake-order-1',at+timedelta(seconds=2),FakeAdapter())
                    outcome='automated'
                except ValueError:
                    pass
                results.append({'case':label,'outcome':outcome,'local_seconds':time.perf_counter()-start})
            finally: store.close()
    return {'cases':results,'automated':sum(x['outcome']=='automated' for x in results),'total':len(results),
            'scope':'Structured, authenticated fixture inputs. Excludes collecting instructions, fact/rights verification, human edits, network deployment and real support labor. 7/10 here is not proof of 70% overall maintenance automation.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',required=True)
    result=trial(); Path(p.parse_args().output).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
