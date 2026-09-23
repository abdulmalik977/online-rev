"""Chicago wall-clock scheduling; all persisted instants are aware UTC."""
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

with (Path(__file__).parent / 'data/Chicago.tzif').open('rb') as f:
    CENTRAL = ZoneInfo.from_file(f, key='America/Chicago')
UTC = timezone.utc


def instant(value):
    value = datetime.fromisoformat(value.replace('Z', '+00:00')) if isinstance(value, str) else value
    if value.tzinfo is None:
        raise ValueError('Timezone-aware instant required')
    return value.astimezone(UTC)


def stamp(value):
    return instant(value).isoformat()


def local_day(value):
    return instant(value).astimezone(CENTRAL).date()


def expiry(generated_at):
    return datetime.combine(local_day(generated_at) + timedelta(days=14), time(), UTC)


def next_slot(at, holidays=(), service=False):
    local = instant(at).astimezone(CENTRAL)
    weekdays = {0, 1, 2, 3, 4} if service else {1, 2, 3}
    windows = [(time(8), time(18))] if service else [(time(8, 30), time(11, 30)), (time(13, 30), time(16))]
    holidays = set(holidays)
    for offset in range(370):
        day = local.date() + timedelta(days=offset)
        if day.weekday() not in weekdays or day.isoformat() in holidays:
            continue
        for begin, end in windows:
            start = datetime.combine(day, begin, CENTRAL)
            stop = datetime.combine(day, end, CENTRAL)
            candidate = max(local, start)
            if candidate < stop:
                return candidate.astimezone(UTC)
    raise ValueError('No eligible slot within one year')


def due(prospect, number, holidays=()):
    if number not in (1, 2, 3):
        raise ValueError('Outreach email number must be 1, 2 or 3')
    first = prospect.get('first_send_at')
    if number > 1 and not first:
        return None
    base = instant(first or prospect['generated_at']).astimezone(CENTRAL)
    candidate = next_slot(base + timedelta(days={1: 0, 2: 3, 3: 8}[number]), holidays)
    return candidate if candidate < instant(prospect['expiry_utc']) - timedelta(hours=24) else None


def service_due(at, holidays=(), cap_reached=False):
    if cap_reached:  # A2 explicitly says next day, even when not a business day.
        day = local_day(at) + timedelta(days=1)
        return datetime.combine(day, time(8), CENTRAL).astimezone(UTC)
    return next_slot(at, holidays, service=True)


def next_business_day(at, holidays=()):
    local = instant(at).astimezone(CENTRAL) + timedelta(days=1)
    return next_slot(local, holidays, service=True)


def cap(first_send, at):
    age = (local_day(at) - local_day(first_send or at)).days + 1
    return 10 if age <= 7 else 20 if age <= 14 else 30 if age <= 21 else 40
