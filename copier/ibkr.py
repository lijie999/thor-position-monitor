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
_account_cache = {}
_portfolio_cache = []


def _on_account_value(value):
    if value.currency in ('USD', ''):
        _account_cache[value.tag] = value.value


def _on_portfolio(item):
    global _portfolio_cache
    _portfolio_cache = list(ib.portfolio())


def connect():
    if ib.isConnected():
        return
    ib.RequestTimeout = 30
    ib.connect(config.IBKR_HOST, config.IBKR_PORT, clientId=config.IBKR_CLIENT_ID, readonly=False, timeout=30)
    log.info(f"IBKR connected: {config.IBKR_HOST}:{config.IBKR_PORT}")

    ib.accountValueEvent += _on_account_value
    ib.updatePortfolioEvent += _on_portfolio

    accts = ib.managedAccounts()
    if accts:
        ib.reqAccountUpdates(subscribe=True, account=accts[0])
        ib.sleep(2)
        log.info(f"Subscribed to account updates: {accts[0]}")


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
    return _portfolio_cache or list(ib.portfolio())


def get_account_values():
    return dict(_account_cache)
