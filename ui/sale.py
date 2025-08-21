# ui/sale.py
import os, sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import tkinter as tk
from tkinter import ttk, messagebox

# services
from services.medicines import search_medicines
from services.invoices  import compute_totals, save_invoice, list_invoices_by_patient
from services.printing  import (
    print_invoice_html,   # HTML only
    open_file             # open in default browser/viewer
)

class SaleFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.cart = []                 # list[dict]: {medicine_id, name, qty, unit_price}
        self._last_invoice_id = None

        self._build_top()
        self._build_cart()
        self._build_summary()

        # Refresh search when the tab gains focus
        self.bind("<FocusIn>", lambda e: self.refresh_search())

    # ---- Top: search + qty + patient ----
    def _build_top(self):
        top = ttk.LabelFrame(self, text="Add Item")
        top.pack(fill="x", padx=10, pady=10)

        self.var_search = tk.StringVar()
        self.var_qty    = tk.StringVar(value="1")
        self.var_pid    = tk.StringVar()   # optional patient id

        ttk.Label(top, text="Search medicine").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        e = ttk.Entry(top, textvariable=self.var_search, width=34)
        e.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        e.bind("<KeyRelease>", self.refresh_search)

        self.lb = tk.Listbox(top, height=6, width=48)
        self.lb.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self.lb.bind("<Double-1>", lambda _e: self.add_to_cart())

        ttk.Label(top, text="Qty").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ttk.Entry(top, textvariable=self.var_qty, width=6).grid(row=0, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(top, text="Patient ID (optional)").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        ttk.Entry(top, textvariable=self.var_pid, width=10).grid(row=0, column=5, padx=5, pady=5, sticky="w")

        # NEW: Patient History button
        ttk.Button(top, text="History", command=self.show_patient_history)\
           .grid(row=0, column=6, padx=6, pady=5, sticky="w")

        ttk.Button(top, text="Add to Cart", command=self.add_to_cart).grid(row=1, column=2, padx=6, pady=5, sticky="w")
        ttk.Button(top, text="Refresh",     command=self.refresh_search).grid(row=1, column=3, padx=6, pady=5, sticky="w")

    # ---- Cart table ----
    def _build_cart(self):
        box = ttk.LabelFrame(self, text="Cart")
        box.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("medicine_id", "name", "qty", "unit_price", "line_total")
        self.table = ttk.Treeview(box, columns=cols, show="headings", height=12)
        for c in cols:
            self.table.heading(c, text=c)
            self.table.column(c, width=140 if c != "name" else 260, anchor="center")
        self.table.pack(fill="both", expand=True)

        bb = ttk.Frame(box); bb.pack(fill="x")
        ttk.Button(bb, text="Remove Selected", command=self.remove_selected).pack(side="left", padx=4, pady=6)
        ttk.Button(bb, text="Clear Cart",      command=self.clear_cart).pack(side="left", padx=4, pady=6)

    # ---- Summary + Save ----
    def _build_summary(self):
        frm = ttk.LabelFrame(self, text="Summary")
        frm.pack(fill="x", padx=10, pady=10)

        self.var_doctor_fee = tk.StringVar(value="0")
        ttk.Label(frm, text="Doctor Fee").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        e = ttk.Entry(frm, textvariable=self.var_doctor_fee, width=10)
        e.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        e.bind("<KeyRelease>", lambda _e: self.update_totals())

        self.lbl_subtotal = ttk.Label(frm, text="Subtotal: 0.00")
        self.lbl_subtotal.grid(row=0, column=2, padx=10, pady=5)
        self.lbl_total = ttk.Label(frm, text="Grand Total: 0.00")
        self.lbl_total.grid(row=0, column=3, padx=10, pady=5)

        ttk.Button(frm, text="Save Invoice", command=self.save_invoice_ui).grid(row=0, column=4, padx=6, pady=5)

    # ---- Events ----
    def refresh_search(self, event=None):
        q = (self.var_search.get() or "").strip()
        self.lb.delete(0, tk.END)
        if not q:
            return
        rows = search_medicines(q)  # id, name, category, unit_price, stock_qty, reorder_level, barcode, active
        for r in rows:
            mid, name, category, unit_price, stock_qty, _, _, _ = r
            self.lb.insert(tk.END, f"{mid} | {name} | Rs {unit_price} | Stock: {stock_qty}")

    def add_to_cart(self):
        sel = self.lb.curselection()
        if not sel:
            messagebox.showerror("Error", "Select a medicine from the list.")
            return

        line = self.lb.get(sel[0])
        parts = [p.strip() for p in line.split("|")]
        mid = int(parts[0]); name = parts[1]
        unit_price = float(parts[2].replace("Rs", "").strip())

        try:
            qty = int(self.var_qty.get())
            if qty <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Error", "Invalid quantity.")
            return

        # Combine if same medicine already in cart
        for it in self.cart:
            if it["medicine_id"] == mid:
                it["qty"] += qty
                self.rebuild_table()
                self.update_totals()
                return

        self.cart.append({"medicine_id": mid, "name": name, "qty": qty, "unit_price": unit_price})
        self.table.insert("", "end", values=(mid, name, qty, unit_price, round(qty * unit_price, 2)))
        self.update_totals()

    def rebuild_table(self):
        for i in self.table.get_children():
            self.table.delete(i)
        for it in self.cart:
            self.table.insert("", "end", values=(
                it["medicine_id"], it["name"], it["qty"], it["unit_price"],
                round(it["qty"] * it["unit_price"], 2)
            ))

    def remove_selected(self):
        sel = self.table.selection()
        if not sel:
            return
        idx = self.table.index(sel[0])
        self.table.delete(sel[0])
        self.cart.pop(idx)
        self.update_totals()

    def clear_cart(self):
        for i in self.table.get_children():
            self.table.delete(i)
        self.cart.clear()
        self.update_totals()

    def update_totals(self):
        subtotal, total, _ = compute_totals(self.cart, self.var_doctor_fee.get())
        self.lbl_subtotal.config(text=f"Subtotal: {subtotal:.2f}")
        self.lbl_total.config(text=f"Grand Total: {total:.2f}")

    def save_invoice_ui(self):
        """Save invoice, then open an HTML invoice for printing (no PDFs)."""
        # 1) Patient ID (optional)
        try:
            pid_txt = (self.var_pid.get() or "").strip()
            pid = int(pid_txt) if pid_txt else None
        except Exception:
            messagebox.showerror("Error", "Patient ID must be a number.")
            return

        try:
            # 2) Save invoice (validates stock & decreases it)
            inv_id, inv_no, subtotal, total, total_items = save_invoice(
                self.cart,
                patient_id=pid,
                doctor_fee=self.var_doctor_fee.get() or 0
            )
            self._last_invoice_id = inv_id

            # 3) Generate HTML invoice and open in default browser (Ctrl+P to print)
            html_path = print_invoice_html(inv_id)
            open_file(html_path)

            # 4) Clear UI & refresh
            self.clear_cart()
            self.var_doctor_fee.set("0")
            self.refresh_search()

            # 5) Confirmation
            messagebox.showinfo(
                "Success",
                f"Invoice saved.\nNumber: {inv_no}\nTotal: {total:.2f}\nItems: {total_items}"
            )

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---- NEW: Patient billing history ----
    def show_patient_history(self):
        pid_txt = (self.var_pid.get() or "").strip()
        if not pid_txt:
            messagebox.showinfo("Patient history", "Enter a Patient ID first.")
            return
        try:
            pid = int(pid_txt)
        except:
            messagebox.showerror("Error", "Patient ID must be a number.")
            return

        rows = list_invoices_by_patient(pid)

        win = tk.Toplevel(self)
        win.title(f"Patient {pid} — Invoices")

        cols  = ("invoice_id","invoice_no","created_at","items","subtotal","doctor_fee","total")
        heads = ["ID","Invoice No","Date/Time","Items","Subtotal","Doctor Fee","Total"]
        tv = ttk.Treeview(win, columns=cols, show="headings", height=14)
        for c, h in zip(cols, heads):
            tv.heading(c, text=h)
            tv.column(c, width=110 if c not in ("invoice_no","created_at") else 170, anchor="center")
        tv.pack(fill="both", expand=True, padx=10, pady=10)

        for (inv_id, inv_no, created, subtotal, doctor_fee, total, total_items) in rows:
            tv.insert("", "end", values=(
                inv_id, inv_no, created, total_items,
                f"{float(subtotal):.2f}", f"{float(doctor_fee):.2f}", f"{float(total):.2f}"
            ))

        btn = ttk.Frame(win); btn.pack(pady=6)
        def _open_selected():
            sel = tv.selection()
            if not sel:
                return
            inv_id = int(tv.item(sel[0], "values")[0])  # first column is invoice_id
            path = print_invoice_html(inv_id)
            open_file(path)
        ttk.Button(btn, text="Open Invoice", command=_open_selected).pack()
