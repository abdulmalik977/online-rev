from datetime import date
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
from threading import Thread
import zipfile

from build import HERE
from expiry_bundle import prepare


class ExpiryTests(unittest.TestCase):
    def test_bundle_removes_all_ten_paths_and_personalized_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'bundle'
            manifest = prepare(HERE / 'testset.csv', dest, date(2026, 9, 22), date(2026, 9, 22))
            self.assertEqual(manifest['expires_at'], '2026-10-06T00:00:00Z')
            self.assertEqual(len(manifest['remove_paths']), 10)
            self.assertFalse(manifest['published'])
            for name, digest in manifest['archive_sha256'].items():
                self.assertEqual(hashlib.sha256((dest / name).read_bytes()).hexdigest(), digest)
            with zipfile.ZipFile(dest / 'expiry.zip') as zipped:
                self.assertEqual(len(zipped.namelist()), 6)
                self.assertFalse(any(n.startswith('previews/') or n.endswith('.json') for n in zipped.namelist()))
                content = '\n'.join(zipped.read(n).decode() for n in zipped.namelist())
                self.assertNotIn('$119', content)
                self.assertNotIn('tel:', content)
                self.assertNotIn("Nick's", content)
            class QuietHandler(SimpleHTTPRequestHandler):
                def log_message(self, *args):
                    pass
            server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(dest / 'expired')))
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                for path in manifest['remove_paths']:
                    with self.assertRaises(HTTPError) as err:
                        urlopen(f'http://127.0.0.1:{server.server_port}' + path, timeout=2)
                    self.assertEqual(err.exception.code, 404)
                    err.exception.close()
            finally:
                server.shutdown(); server.server_close(); thread.join()

    def test_no_overwrite_and_no_expired_or_future_active_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'bundle'
            dest.mkdir()
            with self.assertRaises(ValueError):
                prepare(HERE / 'testset.csv', dest, date(2026, 9, 22), date(2026, 9, 22))
            for now in (date(2026, 9, 21), date(2026, 10, 6)):
                with self.assertRaises(ValueError):
                    prepare(HERE / 'testset.csv', Path(tmp) / 'new', date(2026, 9, 22), now)
            self.assertFalse((Path(tmp) / 'new').exists())


if __name__ == '__main__':
    unittest.main()
