import time
import requests
import logging
import config

log = logging.getLogger('thor_api')

_session = requests.Session()
_session.headers.update({
    'X-API-Key': config.THOR_API_KEY,
    'X-API-Secret': config.THOR_API_SECRET,
})

BASE = config.THOR_BASE_URL + '/api/v1'


def _get(path):
    r = _session.get(BASE + path, timeout=10)
    if r.status_code == 429:
        wait = int(r.json().get('retryAfter', 5))
        log.warning(f"Rate limited, waiting {wait}s...")
        time.sleep(wait)
        r = _session.get(BASE + path, timeout=10)
    r.raise_for_status()
    return r.json()


def get_running_positions():
    return _get('/positions/running').get('positions', [])


def get_closed_positions():
    return _get('/positions/closed').get('closedPositions', [])


def get_connections():
    return _get('/connections').get('connections', [])
