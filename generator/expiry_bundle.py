"""Prepare an active archive and a full replacement expiry archive, without deploying."""
import argparse
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path

from build import HERE, build, load_csv
from deploy import package


def prepare(csv_path, destination, preview_date, today=None):
    today = today or date.today()
    expires = preview_date + timedelta(days=14)
    if not preview_date <= today < expires:
        raise ValueError('Bundle preparation needs a currently active original preview date')
    records = load_csv(csv_path)
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Bundle destination must be new')
    destination.mkdir(parents=True)
    active = destination / 'active'
    expired = destination / 'expired'
    # Deliberately no checkout: session-2 handoff is for review only.
    build(csv_path, active, preview_date, today)
    build(csv_path, expired, preview_date, expires)
    package(active, destination / 'active.zip', today)
    # Preparation of future removal content, not a claim that expiry has run.
    package(expired, destination / 'expiry.zip', expires)
    archives = {name: hashlib.sha256((destination / name).read_bytes()).hexdigest()
                for name in ('active.zip', 'expiry.zip')}
    manifest = dict(schema_version=1, prepared_on=str(today), preview_date=str(preview_date),
                    expires_at=str(expires) + 'T00:00:00Z',
                    input_sha256=hashlib.sha256(Path(csv_path).read_bytes()).hexdigest(),
                    archive_sha256=archives, active_count=len(records), expired_count=0,
                    remove_paths=['/previews/' + r['slug'] + '/' for r in records],
                    deployment_mode='replace_entire_site_tree_not_merge',
                    published=False, remote_expiry_verified=False,
                    acceptance=['At deadline replace active site with expiry.zip',
                                'All remove_paths return HTTP 404 or 410, not a SPA 200 fallback',
                                'No business name, phone, source or checkout remains in public tree',
                                'Verify no-store headers and purge earlier cached active URLs',
                                'Disable old deployment URLs or remove the previous deployment',
                                'Record scheduler result, ten URL statuses and cache checks'])
    (destination / 'expiry-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=HERE / 'testset.csv')
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--preview-date', type=date.fromisoformat, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.input, args.destination, args.preview_date), indent=2))
    except (ValueError, OSError) as error:
        parser.exit(1, f'BUNDLE ERROR: {error}\n')


if __name__ == '__main__':
    main()
