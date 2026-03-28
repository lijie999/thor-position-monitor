MONTH_CODES = {
    'F': '01', 'G': '02', 'H': '03', 'J': '04', 'K': '05', 'M': '06',
    'N': '07', 'Q': '08', 'U': '09', 'V': '10', 'X': '11', 'Z': '12',
}

SYMBOL_MAP = {
    'MNQ': {'ib_symbol': 'MNQ', 'exchange': 'CME', 'multiplier': 2},
    'MES': {'ib_symbol': 'MES', 'exchange': 'CME', 'multiplier': 5},
    'MGC': {'ib_symbol': 'MGC', 'exchange': 'COMEX', 'multiplier': 10},
}


def parse_thor_symbol(thor_symbol):
    base = thor_symbol[:-2]
    month_code = thor_symbol[-2]
    year_digit = thor_symbol[-1]
    year = '202' + year_digit
    month = MONTH_CODES.get(month_code, '01')
    contract_month = year + month
    mapping = SYMBOL_MAP.get(base)
    if not mapping:
        return None
    return {
        'thor_symbol': thor_symbol,
        'ib_symbol': mapping['ib_symbol'],
        'exchange': mapping['exchange'],
        'contract_month': contract_month,
        'multiplier': mapping['multiplier'],
    }


def thor_side_to_action(side):
    if side in (0, '0', 'long', 'Long', 'Buy', 'buy'):
        return 'BUY'
    return 'SELL'


def opposite_action(action):
    return 'SELL' if action == 'BUY' else 'BUY'
