# services/inventory.py
import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from db import get_connection

def stock_in(medicine_id: int, qty: int, reason: str = "Stock-In", ref: str | None = None):
    """
    Increase stock for a medicine and log it in inventory_moves.
    Returns: (medicine_name, new_stock_qty)
    """
    try:
        qty = int(qty)
    except Exception:
        raise ValueError("Quantity must be a number.")
    if qty <= 0:
        raise ValueError("Quantity must be greater than 0.")

    with get_connection() as conn:
        c = conn.cursor()

        row = c.execute("SELECT name, stock_qty, active FROM medicines WHERE id=?", (medicine_id,)).fetchone()
        if not row:
            raise ValueError("Medicine not found.")
        name, stock_qty, active = row
        if not active:
            raise ValueError(f"Medicine '{name}' is inactive.")

        # Update stock
        c.execute("UPDATE medicines SET stock_qty = stock_qty + ? WHERE id=?", (qty, medicine_id))

        # Log move
        c.execute("""
            INSERT INTO inventory_moves (medicine_id, change_qty, reason, ref)
            VALUES (?, ?, ?, ?)
        """, (medicine_id, qty, reason, ref))

        new_qty = c.execute("SELECT stock_qty FROM medicines WHERE id=?", (medicine_id,)).fetchone()[0]
        conn.commit()

    return name, new_qty
