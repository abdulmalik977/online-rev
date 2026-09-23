"""Public identity is derived from the single private company configuration."""
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

PLAN = 'website-monthly-119'
AMOUNT = 11900


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def text(value):
    return isinstance(value,str) and bool(value.strip()) and not re.search(r'[{}\r\n]|YOUR_|\[.+\]',value)


def https(value, production=False):
    if not isinstance(value,str):
        return False
    p=urlsplit(value)
    return (p.scheme=='https' and bool(p.hostname) and not p.username and not p.password
            and not any(c.isspace() or c in '<>"\\' for c in value)
            and (not production or ('.' in p.hostname and not p.hostname.endswith(('.invalid','.test','.localhost')))))


def identity_ready(config):
    return (all(text(config.get(k)) for k in ('company','postal_address','support_email'))
            and re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+',config['support_email']) is not None
            and not config['support_email'].endswith('.invalid')
            and https(config.get('public_base_url'),True))


def checkout_ready(config,evidence):
    return (identity_ready(config) and https(config.get('checkout_base_url'),True)
            and all(evidence.get(k) is True for k in ('provider_eligible','commercial_host','checkout_signed_metadata','order_flow_verified'))
            and evidence.get('checkout_status')==200)
