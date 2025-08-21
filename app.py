import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from db import init_db
from ui.medicines import MedicinesFrame
from ui.patients  import PatientsFrame
from ui.sale      import SaleFrame

# Tools menu helpers
from services.alerts   import low_stock_items
from services.reports  import export_sales_csv_for_date
from services.printing import open_file
from services.inventory import stock_in
from services.medicines import search_medicines


def main():
    init_db()

    root = tk.Tk()
    root.title("Bhatti Clinic")
    root.geometry("1100x700")

    # --- Tabs ---
    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True)

    nb.add(MedicinesFrame(nb), text="Medicines")
    nb.add(PatientsFrame(nb),  text="Patients")
    nb.add(SaleFrame(nb),      text="New Sale")

    # --- Tools menu ---
    menubar = tk.Menu(root)

    def show_low_stock():
        rows = low_stock_items()
        win = tk.Toplevel(root)
        win.title("Low Stock Alerts")

        cols  = ("id", "name", "stock", "reorder", "unit_price")
        heads = ["ID", "Medicine", "Stock", "Reorder", "Unit Price"]

        tv = ttk.Treeview(win, columns=cols, show="headings", height=14)
        for c, h in zip(cols, heads):
            tv.heading(c, text=h)
            tv.column(c, width=120 if c != "name" else 240, anchor="center")
        tv.pack(fill="both", expand=True, padx=10, pady=10)

        for r in rows:
            tv.insert("", "end", values=r)

        if not rows:
            ttk.Label(win, text="Great! No low-stock items.").pack(padx=10, pady=10)

    def export_daily_csv():
        d = simpledialog.askstring(root, "Export Daily Sales",
                                   "Enter date (YYYY-MM-DD):", parent=root)
        if not d:
            return
        try:
            path, totals = export_sales_csv_for_date(d)
            messagebox.showinfo(
                "Export complete",
                f"Saved to:\n{path}\n\n"
                f"Invoices: {totals['count']}\n"
                f"Items: {totals['items']}\n"
                f"Subtotal: {totals['subtotal']:.2f}\n"
                f"Doctor Fee: {totals['doctor_fee']:.2f}\n"
                f"Grand Total: {totals['grand_total']:.2f}"
            )
            open_file(path)
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

    def show_stock_in():
        """Small window to search a medicine and increase its stock."""
        win = tk.Toplevel(root)
        win.title("Stock-In (Increase Stock)")

        frame = ttk.Frame(win); frame.pack(fill="both", expand=True, padx=10, pady=10)

        var_search = tk.StringVar()
        var_qty    = tk.StringVar(value="1")
        var_reason = tk.StringVar(value="Purchase")

        ttk.Label(frame, text="Search medicine").grid(row=0, column=0, sticky="w")
        ent = ttk.Entry(frame, textvariable=var_search, width=34)
        ent.grid(row=0, column=1, padx=6, pady=4, sticky="w")

        ttk.Label(frame, text="Qty (+)").grid(row=0, column=2, sticky="w")
        ttk.Entry(frame, textvariable=var_qty, width=8).grid(row=0, column=3, padx=6, sticky="w")

        ttk.Label(frame, text="Reason").grid(row=0, column=4, sticky="w")
        ttk.Entry(frame, textvariable=var_reason, width=16).grid(row=0, column=5, padx=6, sticky="w")

        lb = tk.Listbox(frame, height=8, width=64)
        lb.grid(row=1, column=0, columnspan=6, sticky="w", padx=0, pady=8)

        def do_search(_e=None):
            q = (var_search.get() or "").strip()
            lb.delete(0, tk.END)
            if not q:
                return
            rows = search_medicines(q)
            for r in rows:
                mid, name, category, unit_price, stock_qty, reorder_level, barcode, active = r
                lb.insert(tk.END, f"{mid} | {name} | Rs {unit_price} | Stock: {stock_qty}")

        ent.bind("<KeyRelease>", do_search)

        def do_stock_in():
            sel = lb.curselection()
            if not sel:
                messagebox.showerror("Error", "Select a medicine from the list.")
                return

            line = lb.get(sel[0])
            parts = [p.strip() for p in line.split("|")]
            try:
                mid = int(parts[0])
            except Exception:
                messagebox.showerror("Error", "Could not read medicine ID."); return

            try:
                q = int(var_qty.get())
                if q <= 0:
                    raise ValueError
            except Exception:
                messagebox.showerror("Error", "Quantity must be a positive number."); return

            reason = (var_reason.get() or "Stock-In").strip()

            try:
                name, new_qty = stock_in(mid, q, reason)
                messagebox.showinfo("Stock updated", f"{name}\nNew stock: {new_qty}")
                do_search()  # refresh list to show updated stock
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(frame, text="Add Stock", command=do_stock_in)\
           .grid(row=2, column=0, sticky="w", pady=6)

        # Start with focus in the search box
        ent.focus_set()

    tools = tk.Menu(menubar, tearoff=0)
    tools.add_command(label="Low Stock Alerts", command=show_low_stock)
    tools.add_command(label="Stock-In (Increase Stock)", command=show_stock_in)
    tools.add_command(label="Export Daily Sales (CSV)", command=export_daily_csv)
    menubar.add_cascade(label="Tools", menu=tools)
    root.config(menu=menubar)
    # --- end Tools menu ---

    root.mainloop()


if __name__ == "__main__":
    main()
