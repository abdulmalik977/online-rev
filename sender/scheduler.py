"""One bounded offline tick; installation/cron and live sending remain disabled."""
from datetime import timedelta
import json
from .calendar import instant,stamp,due


def tick(engine,at,smtp,imap):
    if not getattr(smtp,'offline',False) or not getattr(imap,'offline',False):
        raise PermissionError('Only offline fake transport ticks allowed')
    store=engine.store; conn=store.conn; results=[]
    last=conn.execute("SELECT at FROM audit WHERE action='reconcile_tick' ORDER BY id DESC LIMIT 1").fetchone()
    if not last or instant(at)-instant(last[0])>=timedelta(minutes=30):
        engine.reconcile(at,imap)
        with store.transaction():
            conn.execute('INSERT INTO audit(at,action,detail) VALUES(?,?,?)',(stamp(at),'reconcile_tick','{}'))
    engine.evaluate_bounces(at)
    # Service replies reserve capacity ahead of outreach.
    for row in conn.execute("SELECT * FROM sends WHERE kind='service' AND status IN ('pending','failed') ORDER BY id").fetchall():
        results.append((row['prospect_id'],row['email_no'],engine.dispatch(row['prospect_id'],0,at,smtp,service_job=row['email_no'])))
    for row in conn.execute('SELECT id FROM prospects ORDER BY id').fetchall():
        p=store.get(row['id'])
        if p['state'] not in {'queued','active'}:
            continue
        for number in (1,2,3):
            existing=conn.execute('SELECT status FROM sends WHERE prospect_id=? AND email_no=?',(p['id'],str(number))).fetchone()
            if existing and existing[0]=='sent':
                continue
            result=engine.dispatch(p['id'],number,at,smtp)
            results.append((p['id'],str(number),result))
            if number==3 and result in {'outside_slot','expired'} and due(p,3,engine.holidays) is None:
                key='skip_email3:'+p['id']
                with store.transaction():
                    if not conn.execute('SELECT 1 FROM audit WHERE action=?',(key,)).fetchone():
                        conn.execute('INSERT INTO audit(at,action,detail) VALUES(?,?,?)',(stamp(at),key,json.dumps({'reason':'no_slot_before_fixed_expiry','expiry':p['expiry_utc']})))
            break
    return results
