import asyncio
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from ib_insync import IB, Future, MarketOrder, util
import config
import logging

log = logging.getLogger('ibkr')

ib = IB()


def connect():
    if ib.isConnected():
        return
    ib.RequestTimeout = 30
    ib.connect(config.IBKR_HOST, config.IBKR_PORT, clientId=config.IBKR_CLIENT_ID, readonly=False, timeout=30)
    log.info(f"IBKR connected: {config.IBKR_HOST}:{config.IBKR_PORT}")


def disconnect():
    if ib.isConnected():
        ib.disconnect()


def make_contract(ib_symbol, exchange, contract_month):
    contract = Future(ib_symbol, contract_month, exchange)
    qualified = ib.qualifyContracts(contract)
    if not qualified:
        raise ValueError(f"Cannot qualify contract: {ib_symbol} {contract_month} {exchange}")
    return qualified[0]


def place_order(contract, action, quantity):
    order = MarketOrder(action, quantity)
    trade = ib.placeOrder(contract, order)
    log.info(f"Order placed: {action} {quantity} {contract.localSymbol} -> orderId={trade.order.orderId}")
    ib.sleep(1)
    return trade


def get_positions():
    return ib.positions()


def get_portfolio():
    return ib.portfolio()


def get_account_summary():
    if not ib.isConnected():
        return {}
    ib.reqAccountSummary()
    ib.sleep(1)
    summary = ib.accountSummary()
    result = {}
    for item in summary:
        result[item.tag] = item.value
    ib.cancelAccountSummary()
    return result


def get_account_values():
    if not ib.isConnected():
        return {}
    accts = ib.managedAccounts()
    if not accts:
        return {}
    vals = ib.accountValues(accts[0])
    result = {}
    for v in vals:
        if v.currency in ('USD', ''):
            result[v.tag] = v.value
    return result
