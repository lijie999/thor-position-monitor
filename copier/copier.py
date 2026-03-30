import time
import logging
import signal
import json

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
copier_enabled = True
fixed_quantity = 1
ibkr_connected = False


def handle_signal(sig, frame):
    global running
    log.info("Shutting down...")
    running = False


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


def load_settings():
    global copier_enabled, fixed_quantity
    enabled = db.get_setting('copier_enabled', 'true')
    copier_enabled = enabled.lower() in ('true', '1', 'yes')
    fixed_quantity = int(db.get_setting('fixed_quantity', str(config.FIXED_QUANTITY)))


def get_status():
    return {
        'running': running,
        'copier_enabled': copier_enabled,
        'fixed_quantity': fixed_quantity,
        'ibkr_connected': ibkr_connected,
        'ibkr_port': config.IBKR_PORT,
        'mode': 'PAPER' if config.IBKR_PORT in (4002, 7497) else 'LIVE',
    }


def aggregate_thor_positions(positions):
    agg = {}
    for p in positions:
        symbol = p.get('Symbol', p.get('symbol', ''))
        side = p.get('Side', p.get('side', 0))
        action = thor_side_to_action(side)
        key = f"{symbol}:{action}"
        if key not in agg:
            agg[key] = {
                'symbol': symbol,
                'action': action,
                'total_qty': 0,
                'entry_price': float(p.get('EntryPrice', p.get('entryPrice', 0))),
            }
        agg[key]['total_qty'] += int(p.get('Quantity', p.get('quantity', 0)))
    return agg


def try_connect_ibkr():
    global ibkr_connected
    try:
        ibkr.connect()
        ibkr_connected = True
    except Exception as e:
        ibkr_connected = False
        log.error(f"IBKR connection failed: {e}")


def sync_positions():
    if not copier_enabled:
        return
    if not ibkr_connected:
        try_connect_ibkr()
        if not ibkr_connected:
            return

    try:
        thor_positions = thor_api.get_running_positions()
    except Exception as e:
        log.error(f"Thor API error: {e}")
        return

    thor_agg = aggregate_thor_positions(thor_positions)
    open_trades = db.get_open_trades()

    if thor_agg or open_trades:
        log.info(f"Thor signals: {len(thor_agg)}, DB open: {len(open_trades)}")

    open_trade_symbols = set()

    for trade in open_trades:
        key = f"{trade['symbol']}:{trade['side']}"
        open_trade_symbols.add(key)

        if key not in thor_agg:
            log.info(f"CLOSE: Thor position gone -> {trade['symbol']} {trade['side']}")
            try:
                parsed = parse_thor_symbol(trade['symbol'])
                if not parsed:
                    log.error(f"Unknown symbol: {trade['symbol']}")
                    continue
                contract = ibkr.make_contract(parsed['ib_symbol'], parsed['exchange'], parsed['contract_month'])
                close_action = opposite_action(trade['side'])
                ib_trade = ibkr.place_order(contract, close_action, trade['quantity'])
                db.close_trade(trade['id'], 0, 0, ib_trade.order.orderId)
                log.info(f"CLOSED #{trade['id']} via IBKR order {ib_trade.order.orderId}")
            except Exception as e:
                log.error(f"Failed to close #{trade['id']}: {e}")

    for key, pos in thor_agg.items():
        if key in open_trade_symbols:
            continue

        parsed = parse_thor_symbol(pos['symbol'])
        if not parsed:
            log.warning(f"Unknown symbol {pos['symbol']}, skipping")
            continue

        qty = fixed_quantity
        log.info(f"OPEN: {pos['action']} {qty}x {pos['symbol']} (Thor total: {pos['total_qty']})")

        try:
            contract = ibkr.make_contract(parsed['ib_symbol'], parsed['exchange'], parsed['contract_month'])
            ib_trade = ibkr.place_order(contract, pos['action'], qty)
            trade_id = db.open_trade(
                symbol=pos['symbol'],
                ib_symbol=parsed['ib_symbol'],
                side=pos['action'],
                quantity=qty,
                entry_price=pos['entry_price'],
                ib_order_id=ib_trade.order.orderId,
            )
            log.info(f"OPENED #{trade_id} via IBKR order {ib_trade.order.orderId}")
        except Exception as e:
            log.error(f"Failed to open {pos['symbol']}: {e}")


def run_loop():
    global running
    log.info("=" * 50)
    log.info("Thor -> IBKR Copier")
    log.info(f"IBKR: {config.IBKR_HOST}:{config.IBKR_PORT} ({'PAPER' if config.IBKR_PORT in (4002, 7497) else 'LIVE'})")
    log.info(f"Fixed quantity: {fixed_quantity}")
    log.info(f"Copier enabled: {copier_enabled}")
    log.info("=" * 50)

    try_connect_ibkr()

    while running:
        load_settings()
        sync_positions()
        for _ in range(config.POLL_INTERVAL * 10):
            if not running:
                break
            if ibkr_connected:
                ibkr.ib.sleep(0.1)
            else:
                time.sleep(0.1)

    ibkr.disconnect()
    log.info("Copier stopped")


if __name__ == '__main__':
    run_loop()
