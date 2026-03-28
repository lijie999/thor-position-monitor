import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), 'trades.db')


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thor_account_id TEXT NOT NULL,
            thor_symbol TEXT NOT NULL,
            ib_symbol TEXT,
            side TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            entry_price REAL,
            exit_price REAL,
            entry_time TEXT,
            exit_time TEXT,
            pnl REAL,
            ib_order_id INTEGER,
            ib_close_order_id INTEGER,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
        CREATE INDEX IF NOT EXISTS idx_trades_thor ON trades(thor_account_id, thor_symbol, status);
    """)
    conn.close()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def open_trade(thor_account_id, thor_symbol, ib_symbol, side, quantity, entry_price, ib_order_id):
    conn = get_conn()
    ts = now_iso()
    conn.execute(
        """INSERT INTO trades
           (thor_account_id, thor_symbol, ib_symbol, side, quantity, entry_price, entry_time, ib_order_id, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)""",
        (thor_account_id, thor_symbol, ib_symbol, side, quantity, entry_price, ts, ib_order_id, ts, ts)
    )
    conn.commit()
    trade_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return trade_id


def close_trade(trade_id, exit_price, pnl, ib_close_order_id):
    conn = get_conn()
    ts = now_iso()
    conn.execute(
        """UPDATE trades SET status='closed', exit_price=?, exit_time=?, pnl=?, ib_close_order_id=?, updated_at=?
           WHERE id=?""",
        (exit_price, ts, pnl, ib_close_order_id, ts, trade_id)
    )
    conn.commit()
    conn.close()


def get_open_trades():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM trades WHERE status='open' ORDER BY created_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def find_open_trade(thor_account_id, thor_symbol):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM trades WHERE thor_account_id=? AND thor_symbol=? AND status='open' LIMIT 1",
        (thor_account_id, thor_symbol)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_trades(limit=100):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM trades ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


init_db()
