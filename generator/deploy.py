"""Prepare an allowlisted static archive; no remote publishing before host selection."""
import argparse
from datetime import date
import json
from pathlib import Path
import re
import zipfile

ROOT_FILES = {'index.html', 'style.css', 'expiry.js', 'house.svg', '404.html', '_headers'}


def package(source, archive, today=None):
    source, archive = Path(source), Path(archive)
    if archive.exists():
        raise ValueError('Archive exists; choose a fresh artifact name')
    if source.is_symlink():
        raise ValueError('Symlink source is not allowed')
    report_path = source / 'build-report.json'
    if report_path.is_symlink():
        raise ValueError('Symlink report is not allowed')
    report = json.loads(report_path.read_text(encoding='utf-8'))
    today = today or date.today()
    # Never ship a stale active preview after its expiration or a future-dated build.
    if date.fromisoformat(report['as_of']) > today:
        raise ValueError('Cannot package a future-dated build')
    if today >= date.fromisoformat(report['expires']) and not report['expired']:
        raise ValueError('Expired live content: rebuild with original preview date before packaging')
    files = []
    for path in source.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlinks are not allowed in build output')
        if not path.is_file():
            continue
        relative = path.relative_to(source).as_posix()
        if relative in ROOT_FILES or re.fullmatch(r'previews/[a-z0-9-]+/index\.html', relative):
            files.append((path, relative))
        elif relative not in ('records.json', 'build-report.json'):
            raise ValueError(f'Unexpected file in output: {relative}')
    if not ROOT_FILES <= {r for _, r in files}:
        raise ValueError('Incomplete static assets')
    pages = sum(r.startswith('previews/') for _, r in files)
    if pages != report['active_count']:
        raise ValueError('Preview count differs from build report')
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as bundle:
        for path, relative in sorted(files, key=lambda item: item[1]):
            bundle.write(path, relative)
    return {'archive': str(archive), 'pages': pages, 'files': len(files), 'published': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(package(args.source, args.archive), indent=2))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f'PACKAGE ERROR: {error}\n')


if __name__ == '__main__':
    main()
