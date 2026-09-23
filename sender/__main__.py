"""Read-only gate and private metrics export. No live-send command."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from .gate import checks,load_optional
from .store import Store
from .metrics import export


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['gate','metrics'])
    p.add_argument('--config',default='company/config.json')
    p.add_argument('--evidence',default='.runtime/sender/gate-evidence.json')
    p.add_argument('--db',default='.runtime/sender/sender.sqlite')
    p.add_argument('--output',default='.runtime/sender/pipeline.json')
    args=p.parse_args()
    if args.command=='gate':
        result=checks(load_optional(args.config),load_optional(args.evidence))
        for label,passed in result:
            print(('GREEN' if passed else 'RED')+' '+label)
        return 0 if all(passed for _,passed in result) else 2
    if not Path(args.db).is_file():
        p.error('Sender database does not exist; metrics are not fabricated')
    store=Store(args.db)
    try:
        print(json.dumps(export(store,datetime.now(timezone.utc),args.output),indent=2))
    finally:
        store.close()
    return 0


if __name__=='__main__':
    raise SystemExit(main())
