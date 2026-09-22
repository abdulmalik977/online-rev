"""Deterministic local business concept previews. Standard library only."""
import argparse
import csv
from datetime import date, timedelta
import hashlib
from html import escape
import json
import os
from pathlib import Path
import re
import statistics
from string import Template
import time
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
FIELDS = ('business', 'city', 'state', 'category', 'website', 'phone', 'services',
          'source_url', 'checked_on', 'maps_url', 'maps_status')
SERVICES = {'Plumbing repairs', 'Water heaters', 'Drain cleaning', 'Sewer repairs',
            'Repiping', 'Leak detection', 'Gas lines', 'Air conditioning', 'Heating'}
RESTRICTED = re.compile(r'\b(?:licensed|insured|guaranteed|best|award.winning|same.day)\b|24\s*[/\-]\s*7', re.I)


def https_url(value):
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or
            parsed.password or any(c.isspace() or c in '<>"\\' for c in value)):
        raise ValueError('Expected a public HTTPS URL without credentials')
    return value


def load_csv(path):
    records, seen = [], set()
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(FIELDS):
            raise ValueError('CSV columns/order must match schema.md')
        for line, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f'Row {line}: wrong number of columns')
            row = {key: value.strip() for key, value in row.items()}
            name = row['business']
            if not 2 <= len(name) <= 120 or any(ord(c) < 32 for c in name):
                raise ValueError(f'Row {line}: invalid business name')
            if RESTRICTED.search(name):
                raise ValueError(f'Row {line}: business name needs manual claim review')
            if (row['city'], row['state']) != ('Houston', 'TX'):
                raise ValueError(f'Row {line}: pilot service area must be Houston, TX')
            if row['category'] not in ('plumbing', 'plumbing_hvac'):
                raise ValueError(f'Row {line}: unsupported category')
            https_url(row['website'])
            https_url(row['source_url'])
            checked = date.fromisoformat(row['checked_on'])
            if checked > date.today():
                raise ValueError(f'Row {line}: source check date is in the future')
            if row['phone'] and not re.fullmatch(r'\+1[2-9]\d{9}', row['phone']):
                raise ValueError(f'Row {line}: phone must be US E.164 or blank')
            services = row['services'].split('|')
            if not services or len(set(services)) != len(services) or any(s not in SERVICES for s in services):
                raise ValueError(f'Row {line}: unknown/duplicate service (claims are not free text)')
            if row['category'] == 'plumbing' and {'Heating', 'Air conditioning'} & set(services):
                raise ValueError(f'Row {line}: HVAC service needs plumbing_hvac category')
            if row['maps_status'] not in ('pending', 'checked'):
                raise ValueError(f'Row {line}: invalid Maps status')
            if row['maps_url']:
                host = urlsplit(https_url(row['maps_url'])).hostname
                if host not in ('www.google.com', 'maps.google.com', 'maps.app.goo.gl'):
                    raise ValueError(f'Row {line}: unexpected Maps host')
            if row['maps_status'] == 'checked' and not row['maps_url']:
                raise ValueError(f'Row {line}: checked Maps record requires its source link')
            key = urlsplit(row['website']).hostname.removeprefix('www.')
            if key in seen:
                raise ValueError(f'Row {line}: duplicate business domain')
            seen.add(key)
            digest = hashlib.sha256(name.encode()).hexdigest()
            base = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:65] or 'business'
            row.update(slug=base + '-' + digest[:8], style=int(digest, 16) % 3,
                       services=services,
                       sources={field: row['source_url'] for field in
                                ('business', 'city', 'state', 'category', 'services', 'phone') if row[field]})
            records.append(row)
    if not records:
        raise ValueError('At least one sourced record is required')
    return records


def render(record, preview_date, as_of, checkout=''):
    expires = preview_date + timedelta(days=14)
    if as_of < preview_date:
        raise ValueError('Build date cannot precede preview date')
    if checkout:
        https_url(checkout)
    if as_of >= expires:
        return ('<!doctype html><html lang="en"><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                '<meta name="robots" content="noindex,nofollow,noarchive">'
                '<title>Preview expired</title><h1>This concept preview has expired.</h1></html>')
    e = escape
    services = ''.join(f'<li><span class="service-number">{i:02d}</span><h3>{e(s)}</h3></li>'
                       for i, s in enumerate(record['services'], 1))
    phone = record['phone']
    contact = (f'<a class="button secondary" href="tel:{e(phone)}">Call {e(phone)}</a>' if phone else '')
    purchase = (f'<a class="button" href="{e(checkout)}" rel="noreferrer">Make this my website — $119/month</a>'
                if checkout else '<button class="button" disabled>Make this my website — $119/month</button>'
                '<p class="fine">Checkout is not available during this design preview.</p>')
    maps = (f'<a href="{e(record["maps_url"])}" rel="noreferrer">View business on Google Maps ↗</a>'
            if record['maps_status'] == 'checked' else '')
    content = Template((HERE / 'template.html').read_text(encoding='utf-8'))
    return content.substitute(name=e(record['business']), style=record['style'],
                              initials=e(''.join(w[0] for w in record['business'].split()[:2]).upper()),
                              trade='Plumbing & HVAC' if record['category'] == 'plumbing_hvac' else 'Plumbing',
                              services=services, contact=contact, purchase=purchase,
                              website=e(record['website']), maps=maps, expires=expires.isoformat(),
                              source=e(record['source_url']), checked=e(record['checked_on']))


def build(csv_path, output, preview_date, as_of=None, checkout=''):
    start = time.perf_counter()
    as_of = as_of or date.today()
    records = load_csv(csv_path)
    if checkout:
        https_url(checkout)
    # Validate/render the whole batch before any output mutation.
    rendered, timings = [], []
    for record in records:
        tick = time.perf_counter()
        rendered.append((record, render(record, preview_date, as_of, checkout)))
        timings.append(time.perf_counter() - tick)
    output = Path(output)
    if output.exists():
        raise ValueError('Output must be a new directory; build then replace deployed tree, never merge')
    output.mkdir(parents=True)
    for asset in ('style.css', 'expiry.js', 'house.svg'):
        (output / asset).write_bytes((HERE / asset).read_bytes())
    expired = as_of >= preview_date + timedelta(days=14)
    for record, page in rendered:
        folder = output / 'previews' / record['slug']
        folder.mkdir(parents=True)
        (folder / 'index.html').write_text(page, encoding='utf-8')
    listing = ''.join(f'<li><a href="previews/{r["slug"]}/">{escape(r["business"])}</a></li>' for r in records)
    index_body = '<p>This preview set has expired.</p>' if expired else '<ul>' + listing + '</ul>'
    (output / 'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="robots" content="noindex,nofollow,noarchive"><link rel="stylesheet" href="style.css">'
        '<title>Houston concept previews</title><main class="index"><p class="eyebrow">DESIGN REVIEW</p>'
        '<h1>Houston concept previews</h1><p>Independent, unsolicited concepts. Not official business websites.</p>'
        + index_body + '</main></html>', encoding='utf-8')
    (output / 'records.json').write_text(json.dumps(records, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    report = dict(count=len(records), preview_date=str(preview_date), as_of=str(as_of),
                  expires=str(preview_date + timedelta(days=14)), expired=expired,
                  median_render_seconds=statistics.median(timings), render_seconds=timings,
                  total_build_seconds=time.perf_counter() - start,
                  measurement='Local validation/render/write only; excludes research, QA, deployment and maintenance',
                  live_urls_verified=0, checkout_configured=bool(checkout),
                  maps_checked=sum(r['maps_status'] == 'checked' for r in records))
    (output / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=HERE / 'testset.csv')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--preview-date', type=date.fromisoformat, required=True,
                        help='First preview creation date; never reset it on rebuild')
    parser.add_argument('--as-of', type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.input, args.output, args.preview_date, args.as_of,
                               os.environ.get('CHECKOUT_URL', '')), indent=2))
    except (ValueError, OSError) as error:
        parser.exit(1, f'BUILD ERROR: {error}\n')


if __name__ == '__main__':
    main()
