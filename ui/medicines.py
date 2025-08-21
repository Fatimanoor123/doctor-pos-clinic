# ui/medicines.py
import tkinter as tk
from tkinter import ttk, messagebox
from services.medicines import (
    add_medicine, update_medicine, deactivate_medicine,
    list_medicines, search_medicines
)

class MedicinesFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build_form()
        self._build_table()
        self.reload_table()

    def _build_form(self):
        frm = ttk.LabelFrame(self, text="Medicine Form")
        frm.pack(fill="x", padx=10, pady=10)

        self.var_id = tk.StringVar()
        self.var_name = tk.StringVar()
        self.var_category = tk.StringVar()
        self.var_price = tk.StringVar()
        self.var_stock = tk.StringVar()
        self.var_reorder = tk.StringVar()
        self.var_barcode = tk.StringVar()

        r = 0
        ttk.Label(frm, text="Name*").grid(row=r, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frm, textvariable=self.var_name, width=30).grid(row=r, column=1, padx=5, pady=5)
        ttk.Label(frm, text="Category").grid(row=r, column=2, padx=5, pady=5, sticky="w")
        ttk.Entry(frm, textvariable=self.var_category, width=20).grid(row=r, column=3, padx=5, pady=5)
        r += 1

        ttk.Label(frm, text="Unit Price*").grid(row=r, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frm, textvariable=self.var_price, width=12).grid(row=r, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(frm, text="Stock Qty").grid(row=r, column=2, padx=5, pady=5, sticky="w")
        ttk.Entry(frm, textvariable=self.var_stock, width=10).grid(row=r, column=3, padx=5, pady=5, sticky="w")
        r += 1

        ttk.Label(frm, text="Reorder Level").grid(row=r, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frm, textvariable=self.var_reorder, width=12).grid(row=r, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(frm, text="Barcode").grid(row=r, column=2, padx=5, pady=5, sticky="w")
        ttk.Entry(frm, textvariable=self.var_barcode, width=20).grid(row=r, column=3, padx=5, pady=5, sticky="w")

        btns = ttk.Frame(frm)
        btns.grid(row=0, column=4, rowspan=3, padx=8, pady=5, sticky="ns")
        ttk.Button(btns, text="Add", command=self.do_add).pack(fill="x", pady=2)
        ttk.Button(btns, text="Update", command=self.do_update).pack(fill="x", pady=2)
        ttk.Button(btns, text="Deactivate", command=self.do_deactivate).pack(fill="x", pady=2)
        ttk.Button(btns, text="Clear", command=self.clear_form).pack(fill="x", pady=2)

        # Search bar
        sfrm = ttk.Frame(self)
        sfrm.pack(fill="x", padx=10)
        self.var_search = tk.StringVar()
        ttk.Label(sfrm, text="Search:").pack(side="left")
        se = ttk.Entry(sfrm, textvariable=self.var_search, width=30)
        se.pack(side="left", padx=5, pady=4)
        se.bind("<KeyRelease>", self.on_search)

    def _build_table(self):
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("id","name","category","unit_price","stock_qty","reorder_level","barcode","active")
        self.table = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for c in cols:
            self.table.heading(c, text=c)
            self.table.column(c, width=110 if c != "name" else 220, anchor="center")
        self.table.pack(fill="both", expand=True)

        self.table.bind("<<TreeviewSelect>>", self.on_select)

    def reload_table(self, rows=None):
        for i in self.table.get_children():
            self.table.delete(i)
        rows = rows if rows is not None else list_medicines(include_inactive=True)
        for r in rows:
            self.table.insert("", "end", values=r)

    def on_search(self, e=None):
        q = self.var_search.get().strip()
        if q:
            self.reload_table(search_medicines(q))
        else:
            self.reload_table()

    def do_add(self):
        try:
            if not self.var_name.get().strip():
                messagebox.showerror("Error", "Name is required"); return
            add_medicine(
                self.var_name.get(),
                float(self.var_price.get() or 0),
                int(self.var_stock.get() or 0),
                self.var_category.get() or None,
                int(self.var_reorder.get() or 0),
                self.var_barcode.get() or None
            )
            self.reload_table(); self.clear_form()
            messagebox.showinfo("OK", "Medicine added")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def do_update(self):
        try:
            mid = self.var_id.get()
            if not mid:
                messagebox.showerror("Error", "Select a row first"); return
            update_medicine(
                mid,
                self.var_name.get(),
                float(self.var_price.get() or 0),
                int(self.var_stock.get() or 0),
                self.var_category.get() or None,
                int(self.var_reorder.get() or 0),
                self.var_barcode.get() or None,
                1
            )
            self.reload_table()
            messagebox.showinfo("OK", "Updated")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def do_deactivate(self):
        try:
            mid = self.var_id.get()
            if not mid:
                messagebox.showerror("Error", "Select a row first"); return
            deactivate_medicine(mid)
            self.reload_table(); self.clear_form()
            messagebox.showinfo("OK", "Deactivated")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_form(self):
        self.var_id.set(""); self.var_name.set(""); self.var_category.set("")
        self.var_price.set(""); self.var_stock.set(""); self.var_reorder.set(""); self.var_barcode.set("")

    def on_select(self, e=None):
        sel = self.table.selection()
        if not sel: return
        row = self.table.item(sel[0], "values")
        self.var_id.set(row[0]); self.var_name.set(row[1]); self.var_category.set(row[2])
        self.var_price.set(row[3]); self.var_stock.set(row[4]); self.var_reorder.set(row[5]); self.var_barcode.set(row[6])
