# ui/inventory.py
import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import tkinter as tk
from tkinter import ttk, messagebox
from services.medicines import list_medicines, adjust_stock

class InventoryFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build_stockin()
        self._build_tables()
        self.reload_tables()

    def _build_stockin(self):
        frm = ttk.LabelFrame(self, text="Stock-In")
        frm.pack(fill="x", padx=10, pady=10)

        self.var_mid = tk.StringVar()
        self.var_qty = tk.StringVar(value="1")
        self.var_ref = tk.StringVar()

        ttk.Label(frm, text="Medicine ID").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frm, textvariable=self.var_mid, width=8).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(frm, text="Qty (+)").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ttk.Entry(frm, textvariable=self.var_qty, width=8).grid(row=0, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(frm, text="Ref/Note").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        ttk.Entry(frm, textvariable=self.var_ref, width=18).grid(row=0, column=5, padx=5, pady=5, sticky="w")

        ttk.Button(frm, text="Apply", command=self.stock_in).grid(row=0, column=6, padx=6, pady=5)

    def _build_tables(self):
        # All medicines (active)
        box1 = ttk.LabelFrame(self, text="Medicines (Active)")
        box1.pack(fill="both", expand=True, padx=10, pady=6)

        cols = ("id","name","category","unit_price","stock_qty","reorder_level","barcode","active")
        self.tbl_all = ttk.Treeview(box1, columns=cols, show="headings", height=10)
        for c in cols:
            self.tbl_all.heading(c, text=c)
            self.tbl_all.column(c, width=120 if c!="name" else 220, anchor="center")
        self.tbl_all.pack(fill="both", expand=True)

        # Low stock
        box2 = ttk.LabelFrame(self, text="Low Stock (≤ Reorder Level)")
        box2.pack(fill="both", expand=True, padx=10, pady=6)

        self.tbl_low = ttk.Treeview(box2, columns=cols, show="headings", height=6)
        for c in cols:
            self.tbl_low.heading(c, text=c)
            self.tbl_low.column(c, width=120 if c!="name" else 220, anchor="center")
        self.tbl_low.pack(fill="both", expand=True)

    def reload_tables(self):
        # All
        for i in self.tbl_all.get_children():
            self.tbl_all.delete(i)
        rows = list_medicines(include_inactive=False)
        for r in rows:
            self.tbl_all.insert("", "end", values=r)

        # Low stock: filter rows here
        for i in self.tbl_low.get_children():
            self.tbl_low.delete(i)
        for r in rows:
            _id, _name, _cat, _price, stock, reorder, _barcode, _active = r
            try:
                if int(stock) <= int(reorder):
                    self.tbl_low.insert("", "end", values=r)
            except:
                pass

    def stock_in(self):
        try:
            mid = int(self.var_mid.get())
            qty = int(self.var_qty.get())
            if qty <= 0:
                raise ValueError("Qty must be positive.")
            new_qty = adjust_stock(mid, qty, reason="stock_in", ref=self.var_ref.get() or None)
            self.reload_tables()
            messagebox.showinfo("Done", f"New stock qty: {new_qty}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
