from __future__ import annotations

import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

from db import connect, init_db
from pdf import write_invoice_pdf
from utils import backup_database, ensure_directories, pendrive_available, resolve_base_dir


class MiniERPApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Mini ERP")
        self.geometry("1100x700")
        self.resizable(True, True)

        self.base_dir = resolve_base_dir()
        self.paths = ensure_directories(self.base_dir)
        init_db(self.paths["db"])
        backup_database(self.paths["db"], self.paths["backups"])

        self.status_var = tk.StringVar(value="Ready")

        self._build_ui()
        self._refresh_parties()
        self._refresh_items()
        self._refresh_stock()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.billing_frame = ttk.Frame(notebook)
        self.stock_frame = ttk.Frame(notebook)
        self.party_frame = ttk.Frame(notebook)
        self.report_frame = ttk.Frame(notebook)

        notebook.add(self.billing_frame, text="Billing")
        notebook.add(self.stock_frame, text="Stock")
        notebook.add(self.party_frame, text="Parties")
        notebook.add(self.report_frame, text="Reports")

        self._build_billing_tab()
        self._build_stock_tab()
        self._build_party_tab()
        self._build_report_tab()

        status_bar = ttk.Label(self, textvariable=self.status_var, anchor="w")
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _build_billing_tab(self) -> None:
        form = ttk.LabelFrame(self.billing_frame, text="Invoice Details")
        form.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(form, text="Party").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.invoice_party = ttk.Combobox(form, state="readonly")
        self.invoice_party.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Invoice Date").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.invoice_date = ttk.Entry(form)
        self.invoice_date.grid(row=0, column=3, padx=5, pady=5)
        self.invoice_date.insert(0, datetime.date.today().isoformat())

        item_frame = ttk.LabelFrame(self.billing_frame, text="Add Items")
        item_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(item_frame, text="Item").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.invoice_item = ttk.Combobox(item_frame, state="readonly")
        self.invoice_item.grid(row=0, column=1, padx=5, pady=5)
        self.invoice_item.bind("<<ComboboxSelected>>", self._load_item_rate)

        ttk.Label(item_frame, text="Qty").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.invoice_qty = ttk.Entry(item_frame, width=10)
        self.invoice_qty.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(item_frame, text="Rate").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.invoice_rate = ttk.Entry(item_frame, width=10)
        self.invoice_rate.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(item_frame, text="GST %").grid(row=0, column=6, padx=5, pady=5, sticky=tk.W)
        self.invoice_gst = ttk.Entry(item_frame, width=10)
        self.invoice_gst.grid(row=0, column=7, padx=5, pady=5)

        ttk.Button(item_frame, text="Add Line", command=self._add_invoice_line).grid(
            row=0, column=8, padx=5, pady=5
        )

        self.invoice_lines = ttk.Treeview(
            self.billing_frame,
            columns=("item", "qty", "rate", "gst", "total"),
            show="headings",
            height=8,
        )
        for col, text in zip(
            ("item", "qty", "rate", "gst", "total"),
            ("Item", "Qty", "Rate", "GST%", "Line Total"),
        ):
            self.invoice_lines.heading(col, text=text)
        self.invoice_lines.pack(fill=tk.X, padx=10, pady=10)

        actions = ttk.Frame(self.billing_frame)
        actions.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(actions, text="Remove Line", command=self._remove_invoice_line).pack(
            side=tk.LEFT
        )
        ttk.Button(actions, text="Save Invoice", command=self._save_invoice).pack(
            side=tk.RIGHT
        )

        totals_frame = ttk.Frame(self.billing_frame)
        totals_frame.pack(fill=tk.X, padx=10, pady=10)
        self.subtotal_var = tk.StringVar(value="0.00")
        self.gst_total_var = tk.StringVar(value="0.00")
        self.total_var = tk.StringVar(value="0.00")
        ttk.Label(totals_frame, text="Subtotal:").grid(row=0, column=0, sticky=tk.E)
        ttk.Label(totals_frame, textvariable=self.subtotal_var).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(totals_frame, text="GST:").grid(row=0, column=2, sticky=tk.E)
        ttk.Label(totals_frame, textvariable=self.gst_total_var).grid(row=0, column=3, sticky=tk.W)
        ttk.Label(totals_frame, text="Total:").grid(row=0, column=4, sticky=tk.E)
        ttk.Label(totals_frame, textvariable=self.total_var).grid(row=0, column=5, sticky=tk.W)

    def _build_stock_tab(self) -> None:
        item_form = ttk.LabelFrame(self.stock_frame, text="Items")
        item_form.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(item_form, text="Item Name").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.item_name = ttk.Entry(item_form, width=25)
        self.item_name.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(item_form, text="Opening Stock").grid(
            row=0, column=2, padx=5, pady=5, sticky=tk.W
        )
        self.item_stock = ttk.Entry(item_form, width=10)
        self.item_stock.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(item_form, text="Rate").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.item_rate = ttk.Entry(item_form, width=10)
        self.item_rate.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(item_form, text="GST %").grid(row=0, column=6, padx=5, pady=5, sticky=tk.W)
        self.item_gst = ttk.Entry(item_form, width=10)
        self.item_gst.grid(row=0, column=7, padx=5, pady=5)

        ttk.Label(item_form, text="Low Stock Alert").grid(
            row=0, column=8, padx=5, pady=5, sticky=tk.W
        )
        self.item_low_stock = ttk.Entry(item_form, width=10)
        self.item_low_stock.grid(row=0, column=9, padx=5, pady=5)

        ttk.Button(item_form, text="Add/Update Item", command=self._save_item).grid(
            row=0, column=10, padx=5, pady=5
        )

        purchase_form = ttk.LabelFrame(self.stock_frame, text="Purchase Entry")
        purchase_form.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(purchase_form, text="Item").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.purchase_item = ttk.Combobox(purchase_form, state="readonly")
        self.purchase_item.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(purchase_form, text="Qty").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.purchase_qty = ttk.Entry(purchase_form, width=10)
        self.purchase_qty.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(purchase_form, text="Rate").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.purchase_rate = ttk.Entry(purchase_form, width=10)
        self.purchase_rate.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(purchase_form, text="GST %").grid(row=0, column=6, padx=5, pady=5, sticky=tk.W)
        self.purchase_gst = ttk.Entry(purchase_form, width=10)
        self.purchase_gst.grid(row=0, column=7, padx=5, pady=5)

        ttk.Button(purchase_form, text="Add Purchase", command=self._add_purchase).grid(
            row=0, column=8, padx=5, pady=5
        )

        self.stock_list = ttk.Treeview(
            self.stock_frame,
            columns=("item", "qty", "rate", "gst", "low"),
            show="headings",
        )
        for col, text in zip(
            ("item", "qty", "rate", "gst", "low"),
            ("Item", "Stock", "Rate", "GST%", "Low Alert"),
        ):
            self.stock_list.heading(col, text=text)
        self.stock_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _build_party_tab(self) -> None:
        party_form = ttk.LabelFrame(self.party_frame, text="Add Party")
        party_form.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(party_form, text="Name").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.party_name = ttk.Entry(party_form, width=25)
        self.party_name.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(party_form, text="Type").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.party_type = ttk.Combobox(party_form, values=["Customer", "Supplier"], state="readonly")
        self.party_type.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(party_form, text="Phone").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.party_phone = ttk.Entry(party_form, width=15)
        self.party_phone.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(party_form, text="Email").grid(row=0, column=6, padx=5, pady=5, sticky=tk.W)
        self.party_email = ttk.Entry(party_form, width=20)
        self.party_email.grid(row=0, column=7, padx=5, pady=5)

        ttk.Label(party_form, text="Address").grid(row=0, column=8, padx=5, pady=5, sticky=tk.W)
        self.party_address = ttk.Entry(party_form, width=30)
        self.party_address.grid(row=0, column=9, padx=5, pady=5)

        ttk.Button(party_form, text="Save Party", command=self._save_party).grid(
            row=0, column=10, padx=5, pady=5
        )

        ledger_form = ttk.LabelFrame(self.party_frame, text="Ledger Entry")
        ledger_form.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(ledger_form, text="Party").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.ledger_party = ttk.Combobox(ledger_form, state="readonly")
        self.ledger_party.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(ledger_form, text="Date").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.ledger_date = ttk.Entry(ledger_form, width=12)
        self.ledger_date.grid(row=0, column=3, padx=5, pady=5)
        self.ledger_date.insert(0, datetime.date.today().isoformat())

        ttk.Label(ledger_form, text="Description").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.ledger_desc = ttk.Entry(ledger_form, width=30)
        self.ledger_desc.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(ledger_form, text="Debit").grid(row=0, column=6, padx=5, pady=5, sticky=tk.W)
        self.ledger_debit = ttk.Entry(ledger_form, width=10)
        self.ledger_debit.grid(row=0, column=7, padx=5, pady=5)

        ttk.Label(ledger_form, text="Credit").grid(row=0, column=8, padx=5, pady=5, sticky=tk.W)
        self.ledger_credit = ttk.Entry(ledger_form, width=10)
        self.ledger_credit.grid(row=0, column=9, padx=5, pady=5)

        ttk.Button(ledger_form, text="Add Entry", command=self._add_ledger_entry).grid(
            row=0, column=10, padx=5, pady=5
        )

    def _build_report_tab(self) -> None:
        report_controls = ttk.LabelFrame(self.report_frame, text="Reports")
        report_controls.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(report_controls, text="From (YYYY-MM-DD)").grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.report_from = ttk.Entry(report_controls, width=12)
        self.report_from.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(report_controls, text="To").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.report_to = ttk.Entry(report_controls, width=12)
        self.report_to.grid(row=0, column=3, padx=5, pady=5)

        ttk.Button(report_controls, text="Sales Report", command=self._sales_report).grid(
            row=0, column=4, padx=5, pady=5
        )
        ttk.Button(report_controls, text="Stock Report", command=self._stock_report).grid(
            row=0, column=5, padx=5, pady=5
        )

        ttk.Label(report_controls, text="Ledger Party").grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.report_party = ttk.Combobox(report_controls, state="readonly")
        self.report_party.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(report_controls, text="Ledger Statement", command=self._ledger_report).grid(
            row=1, column=4, padx=5, pady=5
        )

        self.report_output = tk.Text(self.report_frame, height=20)
        self.report_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _refresh_parties(self) -> None:
        with connect(self.paths["db"]) as conn:
            parties = conn.execute("SELECT id, name FROM parties ORDER BY name").fetchall()
        values = [f"{row['id']} - {row['name']}" for row in parties]
        self.invoice_party["values"] = values
        self.ledger_party["values"] = values
        self.report_party["values"] = values

    def _refresh_items(self) -> None:
        with connect(self.paths["db"]) as conn:
            items = conn.execute("SELECT id, name FROM items ORDER BY name").fetchall()
        values = [f"{row['id']} - {row['name']}" for row in items]
        self.invoice_item["values"] = values
        self.purchase_item["values"] = values

    def _refresh_stock(self) -> None:
        for row in self.stock_list.get_children():
            self.stock_list.delete(row)
        with connect(self.paths["db"]) as conn:
            items = conn.execute(
                "SELECT name, stock_qty, rate, gst_percent, low_stock FROM items ORDER BY name"
            ).fetchall()
        for item in items:
            self.stock_list.insert(
                "",
                tk.END,
                values=(
                    item["name"],
                    item["stock_qty"],
                    item["rate"],
                    item["gst_percent"],
                    item["low_stock"],
                ),
            )

    def _load_item_rate(self, _event: tk.Event) -> None:
        item_id = self._selected_id(self.invoice_item.get())
        if not item_id:
            return
        with connect(self.paths["db"]) as conn:
            item = conn.execute(
                "SELECT rate, gst_percent FROM items WHERE id = ?", (item_id,)
            ).fetchone()
        if item:
            self.invoice_rate.delete(0, tk.END)
            self.invoice_rate.insert(0, str(item["rate"]))
            self.invoice_gst.delete(0, tk.END)
            self.invoice_gst.insert(0, str(item["gst_percent"]))

    def _add_invoice_line(self) -> None:
        item_text = self.invoice_item.get()
        qty = self._to_float(self.invoice_qty.get())
        rate = self._to_float(self.invoice_rate.get())
        gst = self._to_float(self.invoice_gst.get())
        if not item_text or qty <= 0:
            messagebox.showwarning("Missing", "Select an item and quantity")
            return
        line_total = qty * rate
        self.invoice_lines.insert(
            "",
            tk.END,
            values=(item_text, f"{qty:.2f}", f"{rate:.2f}", f"{gst:.2f}", f"{line_total:.2f}"),
        )
        self._update_totals()

    def _remove_invoice_line(self) -> None:
        selected = self.invoice_lines.selection()
        for item in selected:
            self.invoice_lines.delete(item)
        self._update_totals()

    def _update_totals(self) -> None:
        subtotal = 0.0
        gst_total = 0.0
        for row in self.invoice_lines.get_children():
            values = self.invoice_lines.item(row)["values"]
            qty = float(values[1])
            rate = float(values[2])
            gst = float(values[3])
            line_total = qty * rate
            subtotal += line_total
            gst_total += line_total * gst / 100
        total = subtotal + gst_total
        self.subtotal_var.set(f"{subtotal:.2f}")
        self.gst_total_var.set(f"{gst_total:.2f}")
        self.total_var.set(f"{total:.2f}")

    def _save_invoice(self) -> None:
        if not pendrive_available(self.base_dir):
            messagebox.showerror("Drive Missing", "Pendrive not available. Please reconnect.")
            return
        if not self.invoice_lines.get_children():
            messagebox.showwarning("Empty", "Add items to invoice")
            return
        party_id = self._selected_id(self.invoice_party.get())
        invoice_date = self.invoice_date.get() or datetime.date.today().isoformat()
        subtotal = float(self.subtotal_var.get())
        gst_total = float(self.gst_total_var.get())
        total = float(self.total_var.get())

        with connect(self.paths["db"]) as conn:
            current_max = conn.execute("SELECT MAX(invoice_no) FROM invoices").fetchone()[0]
            invoice_no = (current_max or 0) + 1
            conn.execute(
                "INSERT INTO invoices (invoice_no, invoice_date, party_id, subtotal, gst_total, total) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (invoice_no, invoice_date, party_id, subtotal, gst_total, total),
            )
            invoice_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            for row in self.invoice_lines.get_children():
                values = self.invoice_lines.item(row)["values"]
                item_id = self._selected_id(values[0])
                qty = float(values[1])
                rate = float(values[2])
                gst = float(values[3])
                line_total = qty * rate
                conn.execute(
                    "INSERT INTO invoice_items (invoice_id, item_id, quantity, rate, gst_percent, line_total) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (invoice_id, item_id, qty, rate, gst, line_total),
                )
                conn.execute(
                    "UPDATE items SET stock_qty = stock_qty - ? WHERE id = ?", (qty, item_id)
                )
                conn.execute(
                    "INSERT INTO sales (item_id, quantity, rate, gst_percent, sale_date, invoice_id) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (item_id, qty, rate, gst, invoice_date, invoice_id),
                )

        invoice_path = self.paths["invoices"] / f"invoice_{invoice_no}.pdf"
        invoice_lines = self._invoice_pdf_lines(invoice_no, invoice_date)
        try:
            write_invoice_pdf(invoice_path, f"Invoice {invoice_no}", invoice_lines)
        except OSError:
            messagebox.showwarning("Invoice", "Invoice saved but PDF export failed.")
        self._clear_invoice_form()
        self._refresh_stock()
        self.status_var.set(f"Invoice {invoice_no} saved")

    def _invoice_pdf_lines(self, invoice_no: int, invoice_date: str) -> list[str]:
        party_label = self.invoice_party.get() or "Walk-in"
        lines = [
            f"Invoice No: {invoice_no}",
            f"Date: {invoice_date}",
            f"Party: {party_label}",
            "",
            "Items:",
        ]
        for row in self.invoice_lines.get_children():
            item, qty, rate, gst, total = self.invoice_lines.item(row)["values"]
            lines.append(f"{item} | Qty {qty} | Rate {rate} | GST {gst}% | Total {total}")
        lines.append("")
        lines.append(f"Subtotal: {self.subtotal_var.get()}")
        lines.append(f"GST Total: {self.gst_total_var.get()}")
        lines.append(f"Grand Total: {self.total_var.get()}")
        return lines

    def _clear_invoice_form(self) -> None:
        for row in self.invoice_lines.get_children():
            self.invoice_lines.delete(row)
        self._update_totals()

    def _save_item(self) -> None:
        name = self.item_name.get().strip()
        if not name:
            messagebox.showwarning("Missing", "Item name required")
            return
        stock = self._to_float(self.item_stock.get())
        rate = self._to_float(self.item_rate.get())
        gst = self._to_float(self.item_gst.get())
        low_stock = self._to_float(self.item_low_stock.get())
        with connect(self.paths["db"]) as conn:
            conn.execute(
                "INSERT INTO items (name, stock_qty, rate, gst_percent, low_stock) "
                "VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(name) DO UPDATE SET stock_qty = excluded.stock_qty, "
                "rate = excluded.rate, gst_percent = excluded.gst_percent, low_stock = excluded.low_stock",
                (name, stock, rate, gst, low_stock),
            )
        self.item_name.delete(0, tk.END)
        self.item_stock.delete(0, tk.END)
        self.item_rate.delete(0, tk.END)
        self.item_gst.delete(0, tk.END)
        self.item_low_stock.delete(0, tk.END)
        self._refresh_items()
        self._refresh_stock()
        self.status_var.set(f"Item {name} saved")

    def _add_purchase(self) -> None:
        item_id = self._selected_id(self.purchase_item.get())
        if not item_id:
            messagebox.showwarning("Missing", "Select an item")
            return
        qty = self._to_float(self.purchase_qty.get())
        rate = self._to_float(self.purchase_rate.get())
        gst = self._to_float(self.purchase_gst.get())
        if qty <= 0:
            messagebox.showwarning("Missing", "Enter quantity")
            return
        purchase_date = datetime.date.today().isoformat()
        with connect(self.paths["db"]) as conn:
            conn.execute(
                "INSERT INTO purchases (item_id, quantity, rate, gst_percent, purchase_date) "
                "VALUES (?, ?, ?, ?, ?)",
                (item_id, qty, rate, gst, purchase_date),
            )
            conn.execute(
                "UPDATE items SET stock_qty = stock_qty + ? WHERE id = ?", (qty, item_id)
            )
        self.purchase_qty.delete(0, tk.END)
        self.purchase_rate.delete(0, tk.END)
        self.purchase_gst.delete(0, tk.END)
        self._refresh_stock()
        self.status_var.set("Purchase added")

    def _save_party(self) -> None:
        name = self.party_name.get().strip()
        party_type = self.party_type.get()
        if not name or not party_type:
            messagebox.showwarning("Missing", "Name and type required")
            return
        with connect(self.paths["db"]) as conn:
            conn.execute(
                "INSERT INTO parties (name, type, phone, email, address) VALUES (?, ?, ?, ?, ?)",
                (
                    name,
                    party_type,
                    self.party_phone.get().strip(),
                    self.party_email.get().strip(),
                    self.party_address.get().strip(),
                ),
            )
        for entry in (
            self.party_name,
            self.party_phone,
            self.party_email,
            self.party_address,
        ):
            entry.delete(0, tk.END)
        self.party_type.set("")
        self._refresh_parties()
        self.status_var.set(f"Party {name} saved")

    def _add_ledger_entry(self) -> None:
        party_id = self._selected_id(self.ledger_party.get())
        if not party_id:
            messagebox.showwarning("Missing", "Select a party")
            return
        entry_date = self.ledger_date.get() or datetime.date.today().isoformat()
        debit = self._to_float(self.ledger_debit.get())
        credit = self._to_float(self.ledger_credit.get())
        with connect(self.paths["db"]) as conn:
            conn.execute(
                "INSERT INTO ledger_entries (party_id, entry_date, description, debit, credit) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    party_id,
                    entry_date,
                    self.ledger_desc.get().strip(),
                    debit,
                    credit,
                ),
            )
        self.ledger_desc.delete(0, tk.END)
        self.ledger_debit.delete(0, tk.END)
        self.ledger_credit.delete(0, tk.END)
        self.status_var.set("Ledger entry saved")

    def _sales_report(self) -> None:
        start = self.report_from.get()
        end = self.report_to.get()
        query = (
            "SELECT invoice_no, invoice_date, total FROM invoices "
            "WHERE invoice_date BETWEEN ? AND ? ORDER BY invoice_date"
        )
        with connect(self.paths["db"]) as conn:
            rows = conn.execute(query, (start, end)).fetchall()
        lines = ["Sales Report", f"From {start} to {end}", ""]
        total_sum = 0.0
        for row in rows:
            lines.append(f"Invoice {row['invoice_no']} | {row['invoice_date']} | {row['total']:.2f}")
            total_sum += row["total"]
        lines.append("")
        lines.append(f"Total Sales: {total_sum:.2f}")
        self._render_report(lines, "sales_report")

    def _stock_report(self) -> None:
        with connect(self.paths["db"]) as conn:
            rows = conn.execute(
                "SELECT name, stock_qty, low_stock FROM items ORDER BY name"
            ).fetchall()
        lines = ["Stock Report", ""]
        for row in rows:
            status = "LOW" if row["stock_qty"] <= row["low_stock"] else "OK"
            lines.append(f"{row['name']} | Qty {row['stock_qty']:.2f} | {status}")
        self._render_report(lines, "stock_report")

    def _ledger_report(self) -> None:
        party_id = self._selected_id(self.report_party.get())
        if not party_id:
            messagebox.showwarning("Missing", "Select a party")
            return
        with connect(self.paths["db"]) as conn:
            party = conn.execute("SELECT name FROM parties WHERE id = ?", (party_id,)).fetchone()
            rows = conn.execute(
                "SELECT entry_date, description, debit, credit FROM ledger_entries "
                "WHERE party_id = ? ORDER BY entry_date",
                (party_id,),
            ).fetchall()
        lines = [f"Ledger Statement: {party['name']}", ""]
        balance = 0.0
        for row in rows:
            balance += row["debit"] - row["credit"]
            lines.append(
                f"{row['entry_date']} | {row['description'] or ''} | "
                f"Dr {row['debit']:.2f} | Cr {row['credit']:.2f} | Bal {balance:.2f}"
            )
        lines.append("")
        lines.append(f"Closing Balance: {balance:.2f}")
        self._render_report(lines, f"ledger_{party_id}")

    def _render_report(self, lines: list[str], report_name: str) -> None:
        report_text = "\n".join(lines)
        self.report_output.delete("1.0", tk.END)
        self.report_output.insert(tk.END, report_text)
        report_path = self.paths["reports"] / f"{report_name}_{datetime.date.today().isoformat()}.txt"
        try:
            report_path.write_text(report_text, encoding="utf-8")
        except OSError:
            self.status_var.set("Report generated but could not be saved")
        else:
            self.status_var.set(f"Report saved: {report_path.name}")

    @staticmethod
    def _selected_id(combo_value: str) -> int | None:
        if not combo_value:
            return None
        try:
            return int(combo_value.split("-")[0].strip())
        except ValueError:
            return None

    @staticmethod
    def _to_float(value: str) -> float:
        try:
            return float(value)
        except ValueError:
            return 0.0


if __name__ == "__main__":
    app = MiniERPApp()
    app.mainloop()
