import csv
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from build import FIELDS, HERE, RESTRICTED, build, load_csv, render
from deploy import package

DAY = date(2026, 9, 22)


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.records = load_csv(HERE / 'testset.csv')

    def changed_csv(self, **changes):
        with (HERE / 'testset.csv').open(encoding='utf-8', newline='') as f:
            row = next(csv.DictReader(f))
        row.update(changes)
        path = self.root / 'changed.csv'
        with path.open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerow(row)
        return path

    def test_ten_real_fixtures_determinism_and_provenance(self):
        a, b = self.root / 'a', self.root / 'b'
        report = build(HERE / 'testset.csv', a, DAY, DAY)
        build(HERE / 'testset.csv', b, DAY, DAY)
        self.assertEqual(report['count'], 10)
        self.assertEqual(len(list(a.glob('previews/*/index.html'))), 10)
        self.assertEqual({r['style'] for r in self.records}, {0, 1, 2})
        for path in a.rglob('*'):
            if path.is_file() and path.name != 'build-report.json':
                self.assertEqual(path.read_bytes(), (b / path.relative_to(a)).read_bytes())
        for record in json.loads((a / 'records.json').read_text(encoding='utf-8')):
            self.assertIn('services', record['sources'])
            page = (a / 'previews' / record['slug'] / 'index.html').read_text(encoding='utf-8')
            self.assertIn('noindex,nofollow,noarchive', page)
            self.assertIn('2026-10-06', page)
            self.assertIn('disabled', page)
            self.assertNotIn('<form', page)
            self.assertFalse(RESTRICTED.search(page))

    def test_untrusted_names_are_escaped_and_paths_are_safe(self):
        path = self.changed_csv(business='../../<script>alert(1)</script> & "Plumber"')
        record = load_csv(path)[0]
        page = render(record, DAY, DAY)
        self.assertNotIn('<script>alert', page)
        self.assertIn('&lt;script&gt;', page)
        self.assertNotIn('/', record['slug'])
        self.assertNotIn('..', record['slug'])

    def test_rejects_unknown_claims_unsafe_urls_bad_phone_and_fake_sources(self):
        cases = ({'services': 'Licensed 24/7 service'}, {'website': 'javascript:alert(1)'},
                 {'source_url': ''}, {'website': 'https://name:secret@example.com'},
                 {'phone': '+123'}, {'city': 'Dallas'}, {'checked_on': '2999-01-01'},
                 {'maps_status': 'checked', 'maps_url': ''},
                 {'maps_url': 'https://evil.example'}, {'category': 'dentist'})
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                load_csv(self.changed_csv(**case))

    def test_duplicate_domain_rejected_before_output(self):
        path = self.root / 'duplicate.csv'
        text = (HERE / 'testset.csv').read_text(encoding='utf-8')
        path.write_text(text + text.splitlines()[1] + '\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            build(path, self.root / 'out', DAY, DAY)
        self.assertFalse((self.root / 'out').exists())

    def test_checkout_is_opt_in_https_and_escaped(self):
        for invalid in ('javascript:alert(1)', 'http://checkout.example', 'https://x.test/" onclick="a'):
            with self.assertRaises(ValueError):
                render(self.records[0], DAY, DAY, invalid)
        page = render(self.records[0], DAY, DAY, 'https://checkout.example/plan?a=1&b=2')
        self.assertIn('a=1&amp;b=2', page)
        self.assertNotIn('disabled', page)

    def test_expiry_boundary_and_no_date_renewal(self):
        record = self.records[0]
        active = render(record, DAY, date(2026, 10, 5))
        expired = render(record, DAY, date(2026, 10, 6))
        self.assertIn('2026-10-06', active)
        self.assertIn('has expired', expired)
        self.assertNotIn(record['website'], expired)
        self.assertNotIn('$119', expired)
        with self.assertRaises(ValueError):
            render(record, DAY, date(2026, 9, 21))

    def test_fresh_output_required_preserves_existing_files(self):
        out = self.root / 'out'
        out.mkdir()
        (out / 'sentinel').write_text('keep')
        with self.assertRaisesRegex(ValueError, 'new directory'):
            build(HERE / 'testset.csv', out, DAY, DAY)
        self.assertEqual((out / 'sentinel').read_text(), 'keep')

    def test_package_allowlist_excludes_internal_json_and_rejects_secret(self):
        out = self.root / 'out'
        build(HERE / 'testset.csv', out, DAY, DAY)
        archive = self.root / 'site.zip'
        self.assertEqual(package(out, archive, DAY)['pages'], 10)
        with zipfile.ZipFile(archive) as zipped:
            self.assertEqual(len(zipped.namelist()), 14)
            self.assertFalse(any(n.endswith('.json') for n in zipped.namelist()))
        (out / '.env').write_text('fake fixture, not a secret')
        with self.assertRaisesRegex(ValueError, 'Unexpected'):
            package(out, self.root / 'bad.zip', DAY)
        self.assertFalse((self.root / 'bad.zip').exists())

    def test_package_rejects_stale_live_content_and_supports_expired_rebuild(self):
        out = self.root / 'out'
        build(HERE / 'testset.csv', out, DAY, DAY)
        with self.assertRaisesRegex(ValueError, 'Expired live content'):
            package(out, self.root / 'stale.zip', date(2026, 10, 6))
        dead = self.root / 'dead'
        build(HERE / 'testset.csv', dead, DAY, date(2026, 10, 6))
        self.assertNotIn(self.records[0]['business'], (dead / 'index.html').read_text())
        self.assertEqual(package(dead, self.root / 'expired.zip', date(2026, 10, 6))['pages'], 10)


if __name__ == '__main__':
    unittest.main()
