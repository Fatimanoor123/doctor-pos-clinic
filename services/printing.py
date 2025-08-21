# services/printing.py
import os, sys, platform, subprocess

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from db import get_connection

# --- Your clinic details (kept as you provided) ---
CLINIC_NAME  = "Bhatti Clinic"
CLINIC_ADDR  = "CB 221/1 Lalazar Wah Cantt"
CLINIC_PHONE = "0300-5497673"
# ---------------------------------------------------

# ---------- Internal helpers ----------
def _fetch_invoice(invoice_id):
    """Return (inv_header_tuple, rows_list) for the invoice."""
    with get_connection() as conn:
        c = conn.cursor()
        inv = c.execute("""
            SELECT i.invoice_no, i.created_at, i.doctor_fee, i.subtotal, i.total, i.total_items,
                   p.name, p.phone
            FROM invoices i LEFT JOIN patients p ON p.id = i.patient_id
            WHERE i.id = ?
        """, (invoice_id,)).fetchone()

        rows = c.execute("""
            SELECT m.name, ii.qty, ii.unit_price, ii.line_total
            FROM invoice_items ii JOIN medicines m ON m.id = ii.medicine_id
            WHERE ii.invoice_id = ?
        """, (invoice_id,)).fetchall()

    if not inv:
        raise ValueError("Invoice not found.")
    return inv, rows

def _ensure_invoice_dir():
    out_dir = os.path.join(ROOT, "data", "invoices")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir
# --------------------------------------


def print_invoice_pdf(invoice_id):
    """
    Create an A4 PDF invoice.
    Raises RuntimeError if ReportLab isn't installed.
    Returns: pdf_path
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
    except ModuleNotFoundError:
        raise RuntimeError(
            "ReportLab not installed. Activate your venv and run: python -m pip install reportlab"
        )

    inv, rows = _fetch_invoice(invoice_id)
    invoice_no, created_at, doctor_fee, subtotal, total, total_items, patient_name, patient_phone = inv

    out_dir = _ensure_invoice_dir()
    pdf_path = os.path.join(out_dir, f"{invoice_no}.pdf")

    cpdf = canvas.Canvas(pdf_path, pagesize=A4)
    w, h = A4
    y = h - 18*mm

    # Header
    cpdf.setFont("Helvetica-Bold", 16); cpdf.drawString(20*mm, y, CLINIC_NAME)
    cpdf.setFont("Helvetica", 9)
    cpdf.drawString(20*mm, y-6*mm, CLINIC_ADDR)
    cpdf.drawString(20*mm, y-11*mm, f"Phone: {CLINIC_PHONE}")
    cpdf.setFont("Helvetica", 10)
    cpdf.drawRightString(190*mm, y,   f"Invoice: {invoice_no}")
    cpdf.drawRightString(190*mm, y-6*mm, f"Date: {created_at}")

    # Patient
    y -= 20*mm
    cpdf.setFont("Helvetica", 10)
    cpdf.drawString(20*mm, y, f"Patient: {patient_name or 'Walk-in'}")
    cpdf.drawString(100*mm, y, f"Phone: {patient_phone or '-'}")

    # Table header
    y -= 10*mm
    cpdf.setFont("Helvetica-Bold", 10)
    cpdf.drawString(20*mm, y, "Item")
    cpdf.drawRightString(120*mm, y, "Qty")
    cpdf.drawRightString(150*mm, y, "Unit")
    cpdf.drawRightString(190*mm, y, "Line Total")
    y -= 4*mm; cpdf.line(20*mm, y, 190*mm, y); y -= 8*mm

    # Rows
    cpdf.setFont("Helvetica", 10)
    for name, qty, unit_price, line_total in rows:
        cpdf.drawString(20*mm, y, str(name))
        cpdf.drawRightString(120*mm, y, str(qty))
        cpdf.drawRightString(150*mm, y, f"{unit_price:.2f}")
        cpdf.drawRightString(190*mm, y, f"{line_total:.2f}")
        y -= 6*mm
        if y < 35*mm:
            cpdf.showPage()
            w, h = A4; y = h - 20*mm
            cpdf.setFont("Helvetica", 10)

    # Totals
    y -= 6*mm; cpdf.line(120*mm, y, 190*mm, y); y -= 8*mm
    cpdf.drawRightString(170*mm, y, "Subtotal:");    cpdf.drawRightString(190*mm, y, f"{subtotal:.2f}")
    y -= 6*mm
    cpdf.drawRightString(170*mm, y, "Doctor Fee:");  cpdf.drawRightString(190*mm, y, f"{doctor_fee:.2f}")
    y -= 6*mm; cpdf.setFont("Helvetica-Bold", 11)
    cpdf.drawRightString(170*mm, y, "Grand Total:"); cpdf.drawRightString(190*mm, y, f"{total:.2f}")

    y -= 10*mm; cpdf.setFont("Helvetica", 9)
    cpdf.drawString(20*mm, y, f"Total quantity of medicines: {total_items}")

    cpdf.save()
    return pdf_path


def print_pdf_to_default_printer(pdf_path: str) -> bool:
    """
    Send a PDF to the default printer.
    Returns True if submitted, False otherwise.
    """
    try:
        if platform.system() == "Windows":
            # Uses the 'print' shell verb via the default PDF app (Adobe Reader recommended)
            os.startfile(pdf_path, "print")  # type: ignore[attr-defined]
            return True
        else:
            # macOS / Linux via CUPS
            r = subprocess.run(["lp", pdf_path], capture_output=True)
            return r.returncode == 0
    except Exception:
        return False


def print_invoice_html(invoice_id):
    """
    Generate a simple, print-ready HTML invoice (no extra packages).
    Returns: html_path
    """
    inv, rows = _fetch_invoice(invoice_id)
    invoice_no, created_at, doctor_fee, subtotal, total, total_items, patient_name, patient_phone = inv

    out_dir = _ensure_invoice_dir()
    html_path = os.path.join(out_dir, f"{invoice_no}.html")

    rows_html = "\n".join(
        f"<tr><td>{name}</td><td class='r'>{qty}</td><td class='r'>{unit_price:.2f}</td><td class='r'>{line_total:.2f}</td></tr>"
        for name, qty, unit_price, line_total in rows
    )

    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>Invoice {invoice_no}</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 20px; }}
  .head {{ display:flex; justify-content:space-between; }}
  .r {{ text-align:right; }}
  table {{ width:100%; border-collapse: collapse; margin-top: 12px; }}
  th, td {{ border:1px solid #999; padding:6px; }}
  .totals {{ width:300px; float:right; margin-top:10px; }}
  @media print {{ body {{ margin: 0.5in; }} }}
</style>
</head>
<body>
  <div class="head">
    <div>
      <h2 style="margin:0;">{CLINIC_NAME}</h2>
      <div>{CLINIC_ADDR}</div>
      <div>Phone: {CLINIC_PHONE}</div>
    </div>
    <div class="r">
      <div><b>Invoice:</b> {invoice_no}</div>
      <div><b>Date:</b> {created_at}</div>
    </div>
  </div>

  <div style="margin-top: 10px;">
    <b>Patient:</b> {patient_name or 'Walk-in'} &nbsp; <b>Phone:</b> {patient_phone or '-'}
  </div>

  <table>
    <thead>
      <tr><th>Item</th><th class="r">Qty</th><th class="r">Unit</th><th class="r">Line Total</th></tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>

  <table class="totals">
    <tr><td>Subtotal</td><td class="r">{subtotal:.2f}</td></tr>
    <tr><td>Doctor Fee</td><td class="r">{doctor_fee:.2f}</td></tr>
    <tr><th>Grand Total</th><th class="r">{total:.2f}</th></tr>
  </table>
</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    return html_path


def open_file(path: str):
    """Open a file in the OS default app (PDF viewer / browser)."""
    try:
        if platform.system() == "Windows":
            os.startfile(path)  # type: ignore[attr-defined]
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass
