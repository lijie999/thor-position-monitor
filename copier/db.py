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
            symbol TEXT NOT NULL,
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
        CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol, status);

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    conn.close()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def get_setting(key, default=None):
    conn = get_conn()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row['value'] if row else default


def set_setting(key, value):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()


def open_trade(symbol, ib_symbol, side, quantity, entry_price, ib_order_id):
    conn = get_conn()
    ts = now_iso()
    conn.execute(
        """INSERT INTO trades
           (symbol, ib_symbol, side, quantity, entry_price, entry_time, ib_order_id, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)""",
        (symbol, ib_symbol, side, quantity, entry_price, ts, ib_order_id, ts, ts)
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


def find_open_trade_by_symbol(symbol):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM trades WHERE symbol=? AND status='open' LIMIT 1", (symbol,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_trades(limit=200):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM trades ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_trade_stats():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) as c FROM trades WHERE status='closed'").fetchone()['c']
    wins = conn.execute("SELECT COUNT(*) as c FROM trades WHERE status='closed' AND pnl > 0").fetchone()['c']
    losses = conn.execute("SELECT COUNT(*) as c FROM trades WHERE status='closed' AND pnl < 0").fetchone()['c']
    gross_win = conn.execute("SELECT COALESCE(SUM(pnl), 0) as s FROM trades WHERE status='closed' AND pnl > 0").fetchone()['s']
    gross_loss = conn.execute("SELECT COALESCE(SUM(pnl), 0) as s FROM trades WHERE status='closed' AND pnl < 0").fetchone()['s']
    net_pnl = conn.execute("SELECT COALESCE(SUM(pnl), 0) as s FROM trades WHERE status='closed'").fetchone()['s']
    open_count = conn.execute("SELECT COUNT(*) as c FROM trades WHERE status='open'").fetchone()['c']
    conn.close()
    return {
        'total': total, 'wins': wins, 'losses': losses,
        'win_rate': round(wins / total * 100, 1) if total > 0 else 0,
        'gross_win': gross_win, 'gross_loss': gross_loss, 'net_pnl': net_pnl,
        'profit_factor': round(gross_win / abs(gross_loss), 2) if gross_loss != 0 else 0,
        'avg_win': round(gross_win / wins, 2) if wins > 0 else 0,
        'avg_loss': round(gross_loss / losses, 2) if losses > 0 else 0,
        'open_count': open_count,
    }


os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
init_db()
