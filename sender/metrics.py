"""Closed-Central-day snapshot. Absence of analytics is null, not zero."""
from datetime import timedelta
import json
from pathlib import Path
from .calendar import local_day, stamp


def snapshot(store,at,analytics_configured=False):
    day=local_day(at)-timedelta(days=1)
    conn=store.conn
    prospects={r[0]:store.get(r[0]) for r in conn.execute('SELECT id FROM prospects')}
    pilot={k for k,p in prospects.items() if not p.get('test') and not p.get('internal')}
    sends=[r for r in conn.execute("SELECT * FROM sends WHERE status='sent' AND kind='outreach'") if r['prospect_id'] in pilot]
    cohort={r['prospect_id'] for r in sends if r['email_no']=='1' and local_day(r['accepted_at'])<=day}
    inbound=[r for r in conn.execute("SELECT * FROM inbound WHERE kind='human'") if r['prospect_id'] in cohort and local_day(r['at'])<=day]
    first={}
    for row in sorted(inbound,key=lambda r:r['at']):
        first.setdefault(row['prospect_id'],json.loads(row['action']))
    positive={k for k,a in first.items() if a.get('reply') in {'ORDER','FAQ_REPLY','ACK_QUESTION','NO_CALL','NO_CALL_ORDER'} and not a.get('suppression') and not set(a.get('queue',[]))&{'legal','refund','uncertain'}}
    orders=[r for r in conn.execute('SELECT * FROM orders') if r['prospect_id'] in cohort and local_day(r['at'])<=day]
    paid={r['prospect_id'] for r in orders}
    daily_inbound=[r for r in inbound if local_day(r['at'])==day]
    views={r['prospect_id'] for r in conn.execute('SELECT * FROM views WHERE excluded=0') if r['prospect_id'] in cohort and local_day(r['at'])==day}
    contacted=len(cohort)
    return dict(schema_version=1,report_day=str(day),timezone='America/Chicago',
                emails_sent=sum(local_day(r['accepted_at'])==day for r in sends),
                replies=len({r['prospect_id'] for r in daily_inbound}),reply_messages=len(daily_inbound),
                sample_views=len(views) if analytics_configured else None,
                paid=sum(local_day(r['at'])==day for r in orders),
                refunded=sum(bool(r['refunded']) for r in orders),
                cohort=dict(unique_prospects_contacted=contacted,replied_prospects=len(first),positive_prospects=len(positive),paid_prospects=len(paid)),
                rates={key:(value/contacted if contacted else None) for key,value in [('reply',len(first)),('positive',len(positive)),('paid',len(paid))]},
                pilot_started_at=min((r['accepted_at'] for r in sends),default=None),
                critical=["Owner queue overdue: "+store.queue_ident(r) for r in conn.execute('SELECT * FROM queue WHERE resolved=0') if r['due'] and r['due']<stamp(at)])


def export(store,at,path,analytics_configured=False):
    data=snapshot(store,at,analytics_configured)
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp'); temp.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8'); temp.replace(path)
    return data


def record_view(store, event_id, prospect_id, at, ip, provider_bot, config):
    import ipaddress
    address=ipaddress.ip_address(ip)
    excluded=provider_bot or any(address in ipaddress.ip_network(cidr) for cidr in config.get('analytics_exclude_ips',[]))
    with store.transaction() as conn:
        store.get(prospect_id)
        conn.execute('INSERT OR IGNORE INTO views VALUES(?,?,?,?)',(event_id,prospect_id,stamp(at),int(excluded)))
