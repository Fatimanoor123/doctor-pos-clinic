# ui/patients.py
import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import tkinter as tk
from tkinter import ttk, messagebox

from services.patients import (
    add_patient, update_patient, deactivate_patient,
    list_patients, search_patients
)

class PatientsFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build_form()
        self._build_table()
        self.reload_table()

    def _build_form(self):
        frm = ttk.LabelFrame(self, text="Patient Form")
        frm.pack(fill="x", padx=10, pady=10)

        self.var_id = tk.StringVar()
        self.var_name = tk.StringVar()
        self.var_age = tk.StringVar()
        self.var_gender = tk.StringVar()
        self.var_phone = tk.StringVar()
        self.var_address = tk.StringVar()

        r = 0
        ttk.Label(frm, text="Name*").grid(row=r, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frm, textvariable=self.var_name, width=28).grid(row=r, column=1, padx=5, pady=5)
        ttk.Label(frm, text="Age").grid(row=r, column=2, padx=5, pady=5, sticky="w")
        ttk.Entry(frm, textvariable=self.var_age, width=8).grid(row=r, column=3, padx=5, pady=5)
        r += 1

        ttk.Label(frm, text="Gender").grid(row=r, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frm, textvariable=self.var_gender, width=10).grid(row=r, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(frm, text="Phone").grid(row=r, column=2, padx=5, pady=5, sticky="w")
        ttk.Entry(frm, textvariable=self.var_phone, width=14).grid(row=r, column=3, padx=5, pady=5, sticky="w")
        r += 1

        ttk.Label(frm, text="Address").grid(row=r, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frm, textvariable=self.var_address, width=50).grid(row=r, column=1, columnspan=3, padx=5, pady=5, sticky="w")

        btns = ttk.Frame(frm)
        btns.grid(row=0, column=4, rowspan=3, padx=10, pady=5, sticky="ns")
        ttk.Button(btns, text="Add", command=self.do_add).pack(fill="x", pady=2)
        ttk.Button(btns, text="Update", command=self.do_update).pack(fill="x", pady=2)
        ttk.Button(btns, text="Deactivate", command=self.do_deactivate).pack(fill="x", pady=2)
        ttk.Button(btns, text="Clear", command=self.clear_form).pack(fill="x", pady=2)

        # Search bar
        sfrm = ttk.Frame(self)
        sfrm.pack(fill="x", padx=10)
        self.var_search = tk.StringVar()
        ttk.Label(sfrm, text="Search by name:").pack(side="left")
        se = ttk.Entry(sfrm, textvariable=self.var_search, width=30)
        se.pack(side="left", padx=6, pady=4)
        se.bind("<KeyRelease>", self.on_search)

    def _build_table(self):
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("id","name","age","gender","phone","address","active")
        self.table = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for c in cols:
            self.table.heading(c, text=c)
            self.table.column(c, width=120 if c not in ("name","address") else 220, anchor="center")
        self.table.pack(fill="both", expand=True)

        self.table.bind("<<TreeviewSelect>>", self.on_select)

    def reload_table(self, rows=None):
        for i in self.table.get_children():
            self.table.delete(i)
        rows = rows if rows is not None else list_patients(include_inactive=True)
        for r in rows:
            self.table.insert("", "end", values=r)

    def on_search(self, e=None):
        q = self.var_search.get().strip()
        if q:
            self.reload_table(search_patients(q))
        else:
            self.reload_table()

    def do_add(self):
        try:
            add_patient(
                self.var_name.get(),
                self.var_age.get(),
                self.var_gender.get(),
                self.var_phone.get(),
                self.var_address.get()
            )
            self.reload_table(); self.clear_form()
            messagebox.showinfo("OK", "Patient added")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def do_update(self):
        try:
            pid = self.var_id.get()
            if not pid:
                messagebox.showerror("Error", "Select a row first"); return
            update_patient(
                pid,
                self.var_name.get(),
                self.var_age.get(),
                self.var_gender.get(),
                self.var_phone.get(),
                self.var_address.get(),
                1
            )
            self.reload_table()
            messagebox.showinfo("OK", "Updated")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def do_deactivate(self):
        try:
            pid = self.var_id.get()
            if not pid:
                messagebox.showerror("Error", "Select a row first"); return
            deactivate_patient(pid)
            self.reload_table(); self.clear_form()
            messagebox.showinfo("OK", "Deactivated")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_form(self):
        self.var_id.set(""); self.var_name.set(""); self.var_age.set("")
        self.var_gender.set(""); self.var_phone.set(""); self.var_address.set("")

    def on_select(self, e=None):
        sel = self.table.selection()
        if not sel: return
        row = self.table.item(sel[0], "values")
        self.var_id.set(row[0]); self.var_name.set(row[1]); self.var_age.set(row[2])
        self.var_gender.set(row[3]); self.var_phone.set(row[4]); self.var_address.set(row[5])
