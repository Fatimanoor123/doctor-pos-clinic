# services/patients.py
# --- path fix so 'db.py' is importable even if you run from VS Code, etc. ---
import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))  # parent folder (project root)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# ---------------------------------------------------------------------------

from db import get_connection

def add_patient(name, age=None, gender=None, phone=None, address=None):
    name = (name or "").strip()
    if not name:
        raise ValueError("Patient name is required.")

    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO patients (name, age, gender, phone, address, active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (
            name,
            int(age) if str(age).strip().isdigit() else None,
            (gender or None),
            (phone or None),
            (address or None),
        ))
        conn.commit()

def update_patient(pid, name, age=None, gender=None, phone=None, address=None, active=1):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE patients
               SET name=?, age=?, gender=?, phone=?, address=?, active=?
             WHERE id=?
        """, (
            (name or "").strip(),
            int(age) if str(age).strip().isdigit() else None,
            (gender or None),
            (phone or None),
            (address or None),
            int(active),
            int(pid),
        ))
        conn.commit()

def deactivate_patient(pid):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("UPDATE patients SET active=0 WHERE id=?", (int(pid),))
        conn.commit()

def list_patients(include_inactive=True):
    with get_connection() as conn:
        c = conn.cursor()
        if include_inactive:
            q = """SELECT id, name, age, gender, phone, address, active
                   FROM patients ORDER BY id DESC"""
        else:
            q = """SELECT id, name, age, gender, phone, address, active
                   FROM patients WHERE active=1 ORDER BY id DESC"""
        return c.execute(q).fetchall()

def search_patients(q):
    q = f"%{(q or '').strip()}%"
    with get_connection() as conn:
        c = conn.cursor()
        return c.execute("""
            SELECT id, name, age, gender, phone, address, active
              FROM patients
             WHERE active=1 AND name LIKE ?
             ORDER BY id DESC
        """, (q,)).fetchall()
