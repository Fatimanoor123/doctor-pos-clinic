# services/invoices.py
# --- path fix so 'db.py' is importable even if you run from VS Code, etc. ---
import os, sys, datetime, sqlite3
ROOT = os.path.dirname(os.path.dirname(__file__))  # parent of 'services'
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# ---------------------------------------------------------------------------

from db import get_connection


def _new_invoice_no():
    """Time-based unique invoice number, e.g., INV-20250817-215959."""
    return "INV-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def compute_totals(cart_items, doctor_fee):
    """
    cart_items: list of dicts -> {"medicine_id": int, "name": str, "qty": int, "unit_price": float}
    doctor_fee: number-ish
    """
    df = float(doctor_fee or 0)
    subtotal = sum(int(it["qty"]) * float(it["unit_price"]) for it in cart_items)
    total_items = sum(int(it["qty"]) for it in cart_items)
    total = round(subtotal + df, 2)
    return round(subtotal, 2), total, total_items


def save_invoice(cart_items, patient_id=None, doctor_fee=0):
    """
    - Validates patient (if provided)
    - Validates stock and refreshes official unit prices from DB
    - Inserts invoice header + line items
    - Decreases stock and logs movement into inventory_moves
    Returns: (invoice_id, invoice_no, subtotal, total, total_items)
    """
    if not cart_items:
        raise ValueError("Cart is empty.")

    # Normalize patient input
    try:
        pid = int(patient_id) if patient_id not in (None, "",) else None
    except:
        raise ValueError("Patient ID must be a number.")

    # Preliminary totals (we'll recompute after refreshing prices)
    subtotal, total, total_items = compute_totals(cart_items, doctor_fee)
    invoice_no = _new_invoice_no()

    with get_connection() as conn:
        c = conn.cursor()
        c.execute("BEGIN")

        # ✅ Validate patient FK early (avoid FOREIGN KEY errors)
        if pid is not None:
            ok = c.execute("SELECT 1 FROM patients WHERE id=? AND active=1", (pid,)).fetchone()
            if not ok:
                conn.rollback()
                raise ValueError(f"Patient ID {pid} not found. Leave it blank or add the patient first.")

        # 1) Validate each medicine, ensure enough stock, and refresh unit_price from DB
        refreshed_items = []
        for it in cart_items:
            mid = int(it["medicine_id"])
            qty = int(it["qty"])

            row = c.execute(
                "SELECT unit_price, stock_qty, active, name FROM medicines WHERE id=?",
                (mid,)
            ).fetchone()
            if not row:
                conn.rollback()
                raise ValueError("Medicine not found.")
            unit_price_db, stock_qty, active, mname = row
            if not active:
                conn.rollback()
                raise ValueError(f"Medicine '{mname}' is inactive.")
            if stock_qty < qty:
                conn.rollback()
                raise ValueError(f"Insufficient stock for {mname}. Available: {stock_qty}, requested: {qty}")

            refreshed_items.append({
                "medicine_id": mid,
                "name": it["name"],
                "qty": qty,
                "unit_price": float(unit_price_db),
                "line_total": round(qty * float(unit_price_db), 2)
            })

        # 2) Recompute totals with official prices
        subtotal = round(sum(x["line_total"] for x in refreshed_items), 2)
        df = float(doctor_fee or 0)
        total_items = sum(x["qty"] for x in refreshed_items)
        total = round(subtotal + df, 2)

        # 3) Insert invoice header
        try:
            c.execute("""
                INSERT INTO invoices (invoice_no, patient_id, doctor_fee, subtotal, total, total_items)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (invoice_no, pid, df, subtotal, total, total_items))
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "FOREIGN KEY" in str(e).upper():
                raise ValueError("Invalid Patient ID. Leave it blank or pick an existing patient.")
            raise
        invoice_id = c.lastrowid

        # 4) Insert items + decrease stock + log movement
        for x in refreshed_items:
            # line item
            c.execute("""
                INSERT INTO invoice_items (invoice_id, medicine_id, qty, unit_price, line_total)
                VALUES (?, ?, ?, ?, ?)
            """, (invoice_id, x["medicine_id"], x["qty"], x["unit_price"], x["line_total"]))

            # decrease stock
            c.execute("UPDATE medicines SET stock_qty = stock_qty - ? WHERE id=?",
                      (x["qty"], x["medicine_id"]))

            # log inventory move (negative for sale)
            c.execute("""
                INSERT INTO inventory_moves (medicine_id, change_qty, reason, ref)
                VALUES (?, ?, 'sale', ?)
            """, (x["medicine_id"], -x["qty"], invoice_no))

        conn.commit()
        return invoice_id, invoice_no, subtotal, total, total_items
def list_invoices_by_patient(patient_id: int):
    """
    Returns rows: (id, invoice_no, created_at, subtotal, doctor_fee, total, total_items)
    newest first.
    """
    with get_connection() as conn:
        c = conn.cursor()
        return c.execute("""
            SELECT id, invoice_no, created_at, subtotal, doctor_fee, total, total_items
            FROM invoices
            WHERE patient_id = ?
            ORDER BY datetime(created_at) DESC
        """, (patient_id,)).fetchall()
