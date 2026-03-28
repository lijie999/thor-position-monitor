import requests
import config

_session = requests.Session()
_session.headers.update({
    'X-API-Key': config.THOR_API_KEY,
    'X-API-Secret': config.THOR_API_SECRET,
})

BASE = config.THOR_BASE_URL + '/api/v1'


def get_running_positions():
    r = _session.get(f'{BASE}/positions/running', timeout=10)
    r.raise_for_status()
    return r.json().get('positions', [])


def get_closed_positions():
    r = _session.get(f'{BASE}/positions/closed', timeout=10)
    r.raise_for_status()
    return r.json().get('closedPositions', [])


def get_connections():
    r = _session.get(f'{BASE}/connections', timeout=10)
    r.raise_for_status()
    return r.json().get('connections', [])
