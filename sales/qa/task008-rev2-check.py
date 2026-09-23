"""Read-only specification probe, NOT a sender or production classifier.

Run from repository root: python sales/qa/task008-rev2-check.py
Outputs extracted flags/FAQ matches and calendar arithmetic as JSON.
No mail, network, state mutation, or claim that all acceptance actions execute.
"""
from datetime import datetime, date, time, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re


SOURCE = Path(__file__).resolve().parents[1] / 'outreach.md'
raw = SOURCE.read_bytes()
doc = raw.decode('utf-8')
flag_section = doc.split('### 5.3 Flags', 1)[1].split('### 5.4', 1)[0]
flags = {}
for name, definition in re.findall(r'^- \*\*([A-Z_]+)\*\*: (.+)$', flag_section, re.M):
    flags[name] = re.findall(r'`([^`]+)`', definition)
assert set(flags) == {'OPT_OUT', 'LEGAL', 'REFUND', 'NOT_NOW', 'NEGATIVE',
                      'INTERESTED', 'CALL', 'QUESTION'}
# Two explicit exceptions in section 5.3: stop and the short affirmative set
# require whole-body equality, not general whole-word matching.
exact_interest = {'yes', 'yes please', 'ok', 'okay', 'sure'}
faq_section = doc.split('## 7. FAQ matching', 1)[1].split('## 8.', 1)[0]
faq = {name: re.findall(r'`([^`]+)`', keywords)
       for name, keywords in re.findall(r'^- \*\*([a-z]+)\*\* \{([^}]+)\}', faq_section, re.M)}
assert len(faq) == 8


def whole(phrase, body):
    return bool(re.search(r'\b' + re.escape(phrase) + r'\b', body))


def inspect(text):
    body = ' '.join(text.lower().split())
    matched = []
    for name, words in flags.items():
        if name == 'QUESTION':
            hit = '?' in body
        elif name == 'OPT_OUT':
            hit = body == 'stop' or any(whole(w, body) for w in words if w not in {'body', 'stop'})
        elif name == 'INTERESTED':
            hit = body in exact_interest or any(whole(w, body) for w in words if w not in exact_interest | {'body'})
        else:
            hit = any(whole(w, body) for w in words)
        if hit:
            matched.append(name)
    return {'body': text, 'flags': matched,
            'faq_matches': [name for name, words in faq.items() if any(whole(w, body) for w in words)]}


texts = {
    '1': 'Yes, interested', '3': 'Can I have a refund?',
    '4': 'Yes, refund please', '5': 'Stop. My lawyer will contact you.',
    '6': 'Please unsubscribe', '7': 'Not now', '8': 'Not interested right now',
    '9': 'I saw it yesterday', '10': 'Can you show my monthly analytics report?',
    '11': 'I am back from out of office; how much?',
    'extra_opt_out_and_interest': 'Unsubscribe. I was interested.',
    'extra_opt_out_and_refund': 'Unsubscribe. Refund please.',
    'extra_plain_negative': 'Not interested',
}
observations = {key: inspect(body) for key, body in texts.items()}

# September/October 2026 fixture is entirely CDT (UTC-05:00); this explicit
# fixed offset does not claim to implement a general America/Chicago calendar.
central_fixture = timezone(timedelta(hours=-5))
initial = datetime(2026, 9, 23, 8, 30, tzinfo=central_fixture)


def first_fixture_slot(holidays):
    due = initial + timedelta(days=8)
    for offset in range(15):
        day = due.date() + timedelta(days=offset)
        if day.weekday() not in {1, 2, 3} or day in holidays:
            continue
        for opening in (time(8, 30), time(13, 30)):
            candidate = datetime.combine(day, opening, central_fixture)
            if candidate >= due:
                return candidate.astimezone(timezone.utc)
    raise AssertionError('No fixture slot')


cutoff = datetime(2026, 10, 6, tzinfo=timezone.utc)
calendar = []
for holidays in (set(), {date(2026, 10, 1)}):
    candidate = first_fixture_slot(holidays)
    calendar.append({'holidays': sorted(map(str, holidays)),
                     'candidate_utc': candidate.isoformat(),
                     'cutoff_utc': cutoff.isoformat(), 'send': candidate < cutoff})

print(json.dumps({'reviewed_commit': '7576955', 'source_sha256': hashlib.sha256(raw).hexdigest(),
                  'scope': 'Keyword/FAQ and two dated calendar probes only; full twenty-row action audit is in outreach-review-round2.md',
                  'text_observations': observations, 'fixture_18': calendar,
                  'complaint_pause': {'max_accepted_sends_per_mailbox_day': 40,
                                      'minimum_denominator': 100, 'reachable': 40 >= 100}}, indent=2))
