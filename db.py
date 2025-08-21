# db.py
import os, sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH  = os.path.join(DATA_DIR, "clinic.db")

def get_connection():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS medicines (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL UNIQUE,
              unit_price REAL NOT NULL CHECK(unit_price >= 0),
              stock_qty INTEGER NOT NULL DEFAULT 0 CHECK(stock_qty >= 0),
              category TEXT,
              reorder_level INTEGER NOT NULL DEFAULT 0,
              barcode TEXT,
              active INTEGER NOT NULL DEFAULT 1
            );
        """)
    
        c.execute("""
        CREATE TABLE IF NOT EXISTS patients (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name   TEXT NOT NULL,
          age    INTEGER,
          gender TEXT,
          phone  TEXT,
          address TEXT,
          active INTEGER NOT NULL DEFAULT 1
        );
    """)
        # ---- Invoices (header) ----
    c.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          invoice_no  TEXT NOT NULL UNIQUE,
          patient_id  INTEGER,
          doctor_fee  REAL NOT NULL DEFAULT 0 CHECK(doctor_fee >= 0),
          subtotal    REAL NOT NULL DEFAULT 0 CHECK(subtotal   >= 0),
          total       REAL NOT NULL DEFAULT 0 CHECK(total      >= 0),
          total_items INTEGER NOT NULL DEFAULT 0,
          created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
          FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
    """)

    # ---- Invoice line items ----
    c.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          invoice_id  INTEGER NOT NULL,
          medicine_id INTEGER NOT NULL,
          qty         INTEGER NOT NULL CHECK(qty > 0),
          unit_price  REAL    NOT NULL CHECK(unit_price >= 0),
          line_total  REAL    NOT NULL CHECK(line_total >= 0),
          FOREIGN KEY (invoice_id)  REFERENCES invoices(id)  ON DELETE CASCADE,
          FOREIGN KEY (medicine_id) REFERENCES medicines(id)
        );
    """)
        # ---- Inventory movements (audit log) ----
    c.execute("""
        CREATE TABLE IF NOT EXISTS inventory_moves (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          medicine_id INTEGER NOT NULL,
          change_qty  INTEGER NOT NULL,           -- + for stock-in, - for sale/adjustment
          reason      TEXT NOT NULL,              -- 'stock_in', 'sale', 'adjustment', 'return'
          ref         TEXT,                       -- invoice_no or note
          created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
          FOREIGN KEY (medicine_id) REFERENCES medicines(id)
        );
    """)
# inventory_moves table (if you don’t have it yet)
    c.execute("""
CREATE TABLE IF NOT EXISTS inventory_moves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id INTEGER NOT NULL,
    change_qty INTEGER NOT NULL,            -- positive for stock-in, negative for stock-out/returns
    reason TEXT,
    ref TEXT,
    created_at TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
)
""")

# Optional but recommended indexes for speed & integrity
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_invoice_no ON invoices(invoice_no)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_invoices_created_at ON invoices(created_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_meds_name ON medicines(name)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_moves_med_created ON inventory_moves(medicine_id, created_at)")

    conn.commit()
