import time
import logging
import signal
import sys

import config
import thor_api
import ibkr
import db
from contracts import parse_thor_symbol, thor_side_to_action, opposite_action

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger('copier')

running = True


def handle_signal(sig, frame):
    global running
    log.info("Shutting down...")
    running = False


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


def build_thor_position_key(pos):
    account_id = pos.get('AccountId', pos.get('accountId', ''))
    symbol = pos.get('Symbol', pos.get('symbol', ''))
    return f"{account_id}:{symbol}"


def sync_positions():
    try:
        thor_positions = thor_api.get_running_positions()
    except Exception as e:
        log.error(f"Thor API error: {e}")
        return

    thor_map = {}
    for p in thor_positions:
        key = build_thor_position_key(p)
        account_id = p.get('AccountId', p.get('accountId', ''))
        symbol = p.get('Symbol', p.get('symbol', ''))
        side = p.get('Side', p.get('side', 0))
        qty = int(p.get('Quantity', p.get('quantity', 0)))
        entry_price = float(p.get('EntryPrice', p.get('entryPrice', 0)))
        thor_map[key] = {
            'account_id': account_id,
            'symbol': symbol,
            'side': side,
            'quantity': qty,
            'entry_price': entry_price,
        }

    open_trades = db.get_open_trades()
    open_trade_keys = set()
    for trade in open_trades:
        key = f"{trade['thor_account_id']}:{trade['thor_symbol']}"
        open_trade_keys.add(key)

        if key not in thor_map:
            log.info(f"CLOSE: Thor position gone -> {key}")
            try:
                parsed = parse_thor_symbol(trade['thor_symbol'])
                if not parsed:
                    log.error(f"Unknown symbol: {trade['thor_symbol']}")
                    continue
                contract = ibkr.make_contract(parsed['ib_symbol'], parsed['exchange'], parsed['contract_month'])
                close_action = opposite_action(trade['side'])
                ib_trade = ibkr.place_order(contract, close_action, trade['quantity'])
                db.close_trade(trade['id'], 0, 0, ib_trade.order.orderId)
                log.info(f"CLOSED trade #{trade['id']} via IBKR order {ib_trade.order.orderId}")
            except Exception as e:
                log.error(f"Failed to close trade #{trade['id']}: {e}")

    for key, pos in thor_map.items():
        if key in open_trade_keys:
            continue

        parsed = parse_thor_symbol(pos['symbol'])
        if not parsed:
            log.warning(f"Unknown symbol {pos['symbol']}, skipping")
            continue

        action = thor_side_to_action(pos['side'])
        log.info(f"OPEN: New Thor position -> {key} {action} {pos['quantity']}x {pos['symbol']}")

        try:
            contract = ibkr.make_contract(parsed['ib_symbol'], parsed['exchange'], parsed['contract_month'])
            ib_trade = ibkr.place_order(contract, action, pos['quantity'])
            trade_id = db.open_trade(
                thor_account_id=pos['account_id'],
                thor_symbol=pos['symbol'],
                ib_symbol=parsed['ib_symbol'],
                side=action,
                quantity=pos['quantity'],
                entry_price=pos['entry_price'],
                ib_order_id=ib_trade.order.orderId,
            )
            log.info(f"OPENED trade #{trade_id} via IBKR order {ib_trade.order.orderId}")
        except Exception as e:
            log.error(f"Failed to open trade for {key}: {e}")


def main():
    log.info("=" * 50)
    log.info("Thor -> IBKR Copier starting")
    log.info(f"IBKR: {config.IBKR_HOST}:{config.IBKR_PORT} ({'PAPER' if config.IBKR_PORT == 4002 else 'LIVE'})")
    log.info(f"Poll interval: {config.POLL_INTERVAL}s")
    log.info("=" * 50)

    ibkr.connect()

    log.info(f"Open trades in DB: {len(db.get_open_trades())}")
    log.info("Monitoring Thor positions...")

    while running:
        sync_positions()
        for _ in range(config.POLL_INTERVAL * 10):
            if not running:
                break
            time.sleep(0.1)

    ibkr.disconnect()
    log.info("Copier stopped")


if __name__ == '__main__':
    main()
