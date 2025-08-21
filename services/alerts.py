# services/alerts.py
import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from db import get_connection

def low_stock_items():
    """
    Returns rows: (id, name, stock_qty, reorder_level, unit_price)
    for medicines with stock <= reorder_level and active=1.
    """
    with get_connection() as conn:
        c = conn.cursor()
        rows = c.execute("""
            SELECT id, name, stock_qty, reorder_level, unit_price
            FROM medicines
            WHERE active=1 AND stock_qty <= reorder_level
            ORDER BY stock_qty ASC, name ASC
        """).fetchall()
    return rows
