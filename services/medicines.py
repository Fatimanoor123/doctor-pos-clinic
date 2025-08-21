# --- add these lines at the very top ---
import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))  # parent of 'services'
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# ---------------------------------------
from db import get_connection

def add_medicine(name, unit_price, stock_qty=0, category=None, reorder_level=0, barcode=None):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO medicines (name, unit_price, stock_qty, category, reorder_level, barcode, active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (name.strip(), float(unit_price), int(stock_qty or 0),
              category, int(reorder_level or 0), barcode))
        conn.commit()

def update_medicine(mid, name, unit_price, stock_qty, category=None, reorder_level=0, barcode=None, active=1):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE medicines
            SET name=?, unit_price=?, stock_qty=?, category=?, reorder_level=?, barcode=?, active=?
            WHERE id=?
        """, (name.strip(), float(unit_price), int(stock_qty), category,
              int(reorder_level or 0), barcode, int(active), int(mid)))
        conn.commit()

def deactivate_medicine(mid):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("UPDATE medicines SET active=0 WHERE id=?", (int(mid),))
        conn.commit()

def list_medicines(include_inactive=True):
    with get_connection() as conn:
        c = conn.cursor()
        if include_inactive:
            q = """SELECT id, name, category, unit_price, stock_qty, reorder_level, barcode, active
                   FROM medicines ORDER BY name"""
        else:
            q = """SELECT id, name, category, unit_price, stock_qty, reorder_level, barcode, active
                   FROM medicines WHERE active=1 ORDER BY name"""
        return c.execute(q).fetchall()

def search_medicines(q):
    q = f"%{q.strip()}%"
    with get_connection() as conn:
        c = conn.cursor()
        return c.execute("""
          SELECT id, name, category, unit_price, stock_qty, reorder_level, barcode, active
          FROM medicines
          WHERE active=1 AND name LIKE ?
          ORDER BY name
        """, (q,)).fetchall()
        
        
        
def adjust_stock(medicine_id, delta, reason="adjustment", ref=None):
    """
    delta: +ve for stock-in, -ve for sale/return/adjustment
    Ensures stock never goes negative and logs the move.
    """
    with get_connection() as conn:
        c = conn.cursor()
        row = c.execute("SELECT stock_qty, name FROM medicines WHERE id=? AND active=1",
                        (int(medicine_id),)).fetchone()
        if not row:
            raise ValueError("Medicine not found or inactive.")
        stock_qty, name = row
        new_qty = stock_qty + int(delta)
        if new_qty < 0:
            raise ValueError(f"Insufficient stock for {name}. Available: {stock_qty}, need: {abs(delta)}")

        c.execute("UPDATE medicines SET stock_qty=? WHERE id=?", (new_qty, int(medicine_id)))
        c.execute("""
            INSERT INTO inventory_moves (medicine_id, change_qty, reason, ref)
            VALUES (?, ?, ?, ?)
        """, (int(medicine_id), int(delta), reason, ref))
        conn.commit()
        return new_qty
