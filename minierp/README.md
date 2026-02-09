# MiniERP (Portable Offline)

## Overview
MiniERP is a fully portable, offline ERP-style desktop app written in Python using Tkinter and SQLite. It runs directly from a USB drive without installation, keeps all data in a single `database.db` file on the drive, and exports invoices/reports to folders on the same drive.

## Folder Structure
```
/MiniERP
  ├─ app.exe
  ├─ database.db
  ├─ backups/
  ├─ invoices/
  └─ reports/
```

When running from source, the app expects these folders next to `app.py`.

## Database Schema
See `schema.sql` for the full schema. Tables include:
- `items` for stock
- `parties` for customers/suppliers
- `ledger_entries`
- `invoices` and `invoice_items`
- `purchases` and `sales`

## GUI Layout (Explanation)
The UI uses a `ttk.Notebook` with four tabs:
1. **Billing**
   - Party selector, invoice date
   - Item entry (item, qty, rate, GST%)
   - Invoice lines grid and totals
   - Save invoice and export PDF
2. **Stock**
   - Item creation/update (opening stock, rate, GST%, low stock threshold)
   - Purchase entry to increase stock
   - Stock listing with low-stock indicator
3. **Parties**
   - Customer/Supplier creation
   - Ledger entry posting (debit/credit)
4. **Reports**
   - Sales report by date range
   - Stock report (low stock alerts)
   - Ledger statement per party

Reports are displayed in the UI and saved into the `reports/` folder as text files.

## Portable Design Notes
- **No installation**: The app uses relative paths and runs from the USB drive.
- **Offline storage**: SQLite database is stored as `database.db` on the drive.
- **Automatic backups**: Each launch copies the database into `backups/` with a timestamp.
- **Drive removal handling**: The app checks drive availability before saving invoices and reports.

## Build a Portable EXE (PyInstaller)
1. Install dependencies on a build machine (not required on target PCs):
   ```bash
   pip install pyinstaller
   ```
2. From the `minierp` folder, run:
   ```bash
   pyinstaller --noconsole --onefile app.py --name app
   ```
3. Copy the generated `dist/app.exe` into your USB `MiniERP` folder.
4. Ensure the following structure exists on the USB drive:
   ```
   /MiniERP
     ├─ app.exe
     ├─ database.db (auto-created on first run)
     ├─ backups/
     ├─ invoices/
     └─ reports/
   ```
5. Run `app.exe` on any Windows PC. No installation required.

## Running from Source
```
python app.py
```

## Notes
- PDF export uses a lightweight built-in PDF generator (no external libraries).
- Keep the USB drive connected while saving invoices or reports.
