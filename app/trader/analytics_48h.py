#!/usr/bin/env python3
"""
48h Trading Performance Analysis
Computes win rate per strategy, top signals, and issues.
"""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import json

DB_PATH = '/root/mirai-agent/state/mirai.db'

def analyze_last_48h(db_path: str = DB_PATH) -> dict:
    now = datetime.utcnow()
    since = now - timedelta(hours=48)
    result = {
        'timestamp': now.isoformat(),
        'window_start': since.isoformat(),
        'strategies': {},
        'summary': {}
    }

    if not Path(db_path).exists():
        result['error'] = 'database_not_found'
        return result

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Try trades table first
    try:
        c.execute("""
            SELECT strategy, COUNT(*) as n,
                   SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                   SUM(pnl) as total_pnl
            FROM trades
            WHERE datetime(created_at) >= datetime(?)
            GROUP BY strategy
        """, (since.isoformat(),))
        rows = c.fetchall()
        total_trades = 0
        total_pnl = 0.0
        for strategy, n, wins, total_p in rows:
            win_rate = (wins or 0) / n * 100 if n else 0
            result['strategies'][strategy or 'unknown'] = {
                'trades': n,
                'wins': wins or 0,
                'win_rate': round(win_rate, 2),
                'pnl': round(total_p or 0.0, 2)
            }
            total_trades += n
            total_pnl += total_p or 0.0
        result['summary'] = {
            'total_trades': total_trades,
            'total_pnl': round(total_pnl, 2)
        }
    except Exception:
        # Fallback: derive from risk_events POSITION_CLOSED messages
        try:
            c.execute("""
                SELECT description
                FROM risk_events
                WHERE datetime(timestamp) >= datetime(?)
            """, (since.isoformat(),))
            rows = c.fetchall()
            wins = losses = 0
            for (desc,) in rows:
                if not desc:
                    continue
                if 'P&L $' in desc:
                    try:
                        pnl_str = desc.split('P&L $')[1].split(' ')[0].replace(',', '')
                        pnl = float(pnl_str)
                        if pnl > 0:
                            wins += 1
                        elif pnl < 0:
                            losses += 1
                    except Exception:
                        pass
            n = wins + losses
            result['strategies']['all'] = {
                'trades': n,
                'wins': wins,
                'win_rate': round((wins / n * 100) if n else 0, 2),
                'pnl': None
            }
            result['summary'] = {'total_trades': n}
        except Exception as e:
            result['error'] = str(e)
    finally:
        conn.close()

    return result

if __name__ == '__main__':
    report = analyze_last_48h()
    print(json.dumps(report, indent=2))

