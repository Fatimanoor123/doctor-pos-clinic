# services/reports.py
import os, sys, csv, datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from db import get_connection

def export_sales_csv_for_date(date_str: str):
    """
    Export all invoices for the given local date (YYYY-MM-DD) to data/reports/sales_YYYYMMDD.csv.
    Returns (path, totals_dict).
    """
    try:
        day = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        raise ValueError("Date must be in YYYY-MM-DD format.")

    out_dir = os.path.join(ROOT, "data", "reports")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"sales_{day.strftime('%Y%m%d')}.csv")

    with get_connection() as conn:
        c = conn.cursor()
        rows = c.execute("""
            SELECT i.invoice_no,
                   i.created_at,
                   IFNULL(p.name, 'Walk-in') AS patient_name,
                   i.total_items,
                   i.subtotal,
                   i.doctor_fee,
                   i.total
            FROM invoices i
            LEFT JOIN patients p ON p.id = i.patient_id
            WHERE DATE(i.created_at) = DATE(?)
            ORDER BY datetime(i.created_at) ASC
        """, (day.isoformat(),)).fetchall()

    totals = {
        "count": len(rows),
        "items": sum(int(r[3]) for r in rows),
        "subtotal": sum(float(r[4]) for r in rows),
        "doctor_fee": sum(float(r[5]) for r in rows),
        "grand_total": sum(float(r[6]) for r in rows),
    }

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Invoice No","Datetime","Patient","Items Qty","Subtotal","Doctor Fee","Grand Total"])
        for r in rows:
            w.writerow(r)
        w.writerow([])
        w.writerow(["Invoices", totals["count"]])
        w.writerow(["Total items", totals["items"]])
        w.writerow(["Subtotal", f"{totals['subtotal']:.2f}"])
        w.writerow(["Doctor Fee", f"{totals['doctor_fee']:.2f}"])
        w.writerow(["Grand Total", f"{totals['grand_total']:.2f}"])

    return out_path, totals
