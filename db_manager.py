import sqlite3
import bcrypt
import time
from datetime import datetime

# --- DATABASE CONNECTION FUNCTIONS ---

def get_officer_conn():
    # Connects to the officers database
    conn = sqlite3.connect('officers.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_log_conn():
    # Connects to the audit log database
    conn = sqlite3.connect('audit_log.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- INITIAL SETUP FUNCTIONS (Run Once) ---

def create_tables():
    # 1. Officers Table for Authentication
    conn = get_officer_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS officers (
            badge_number TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            password_hash BLOB NOT NULL
        )
    """)
    conn.commit()
    conn.close()

    # 2. Audit Log Table for tracking changes
    conn = get_log_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT NOT NULL,
            badge_number TEXT NOT NULL,
            change_type TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            change_detail TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_test_officer(badge, name, email, password):
    conn = get_officer_conn()
    
    # Generate a secure hash for the password
    password_bytes = password.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    
    try:
        conn.execute(
            "INSERT INTO officers (badge_number, full_name, email, password_hash) VALUES (?, ?, ?, ?)",
            (badge, name, email, hashed_password)
        )
        conn.commit()
        print(f"Officer {name} ({badge}) added successfully.")
    except sqlite3.IntegrityError:
        print(f"Error: Officer with badge {badge} already exists.")
    finally:
        conn.close()

# --- AUTHENTICATION CHECK FUNCTION ---

def verify_officer_login(badge, password):
    conn = get_officer_conn()
    cursor = conn.execute("SELECT full_name, email, password_hash FROM officers WHERE badge_number = ?", (badge,))
    user_record = cursor.fetchone()
    conn.close()

    if user_record:
        # Check the entered password against the stored hash
        stored_hash = user_record['password_hash']
        
        # Check if the entered password matches the stored hash
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return True, user_record['full_name'], user_record['email']
    
    return False, None, None

# --- AUDIT LOGGING FUNCTION ---

def log_change(report_id, badge_number, change_type, change_detail):
    conn = get_log_conn()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn.execute(
        "INSERT INTO audit_log (report_id, badge_number, change_type, timestamp, change_detail) VALUES (?, ?, ?, ?, ?)",
        (report_id, badge_number, change_type, current_time, change_detail)
    )
    conn.commit()
    log_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return log_id

# Execute initial setup when script is run directly
if __name__ == '__main__':
    create_tables()
    # ADD YOUR INITIAL OFFICER(S) HERE FOR TESTING
    add_test_officer('1001', 'John R. Smith', 'john.smith@police.gov', 'testpass') 
    add_test_officer('1002', 'Jane D. Doe', 'jane.doe@police.gov', 'secure02')
    print("Database setup complete. Ready to run app.py.")