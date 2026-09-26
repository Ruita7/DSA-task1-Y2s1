import sqlite3


class Database:
    """Handles persistent SQLite database operations."""

    def __init__(self, db_name: str):
        self.db_name = db_name
        self.connection = sqlite3.connect(db_name, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.create_tables()

    def _add_column_if_missing(self, table, column, definition):
        columns = {
            row[1] for row in self.connection.execute(f"PRAGMA table_info({table})")
        }
        if column not in columns:
            self.connection.execute(
                f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
            )

    def create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parking_slots (
                slot_number INTEGER PRIMARY KEY,
                status TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                plate_number TEXT PRIMARY KEY,
                vehicle_type TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parking_records (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT NOT NULL,
                slot_number INTEGER NOT NULL,
                arrival_time TEXT NOT NULL,
                exit_time TEXT,
                duration_hours INTEGER,
                fee REAL DEFAULT 0,
                payment_status TEXT NOT NULL DEFAULT 'Unpaid',
                tax_amount REAL DEFAULT 0,
                total_due REAL DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_time TEXT NOT NULL,
                status TEXT NOT NULL,
                transaction_reference TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mpesa_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER,
                plate_number TEXT NOT NULL,
                checkout_request_id TEXT UNIQUE,
                merchant_request_id TEXT,
                amount REAL NOT NULL,
                phone_number TEXT NOT NULL,
                result_code TEXT,
                result_description TEXT,
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TEXT NOT NULL
            )
        """)

        # Upgrade databases created by the earlier version.
        self._add_column_if_missing("parking_records", "tax_amount", "REAL DEFAULT 0")
        self._add_column_if_missing("parking_records", "total_due", "REAL DEFAULT 0")
        self._add_column_if_missing("payments", "transaction_reference", "TEXT")
        self.connection.execute(
            "UPDATE parking_records SET total_due = fee WHERE total_due IS NULL OR total_due = 0"
        )
        self.connection.commit()

    def save_slot(self, slot_number, status):
        self.connection.execute(
            """INSERT INTO parking_slots(slot_number, status) VALUES (?, ?)
               ON CONFLICT(slot_number) DO UPDATE SET status = excluded.status""",
            (slot_number, status),
        )
        self.connection.commit()

    def save_vehicle(self, plate_number, vehicle_type):
        self.connection.execute(
            "INSERT OR REPLACE INTO vehicles(plate_number, vehicle_type) VALUES (?, ?)",
            (plate_number, vehicle_type),
        )
        self.connection.commit()

    def create_parking_record(self, plate_number, slot_number, arrival_time):
        cursor = self.connection.cursor()
        cursor.execute(
            """INSERT INTO parking_records
               (plate_number, slot_number, arrival_time, payment_status, fee, tax_amount, total_due)
               VALUES (?, ?, ?, 'Unpaid', 0, 0, 0)""",
            (plate_number, slot_number, arrival_time.isoformat()),
        )
        self.connection.commit()
        return cursor.lastrowid

    def close_parking_record(self, record_id, exit_time, duration_hours, fee, tax_amount, total_due):
        self.connection.execute(
            """UPDATE parking_records
               SET exit_time = ?, duration_hours = ?, fee = ?, tax_amount = ?, total_due = ?
               WHERE record_id = ?""",
            (exit_time.isoformat(), duration_hours, fee, tax_amount, total_due, record_id),
        )
        self.connection.commit()

    def record_payment(self, record_id, amount, payment_time, status, transaction_reference=None):
        self.connection.execute(
            """INSERT INTO payments
               (record_id, amount, payment_time, status, transaction_reference)
               VALUES (?, ?, ?, ?, ?)""",
            (record_id, amount, payment_time.isoformat(), status, transaction_reference),
        )
        if status == "Paid":
            self.connection.execute(
                "UPDATE parking_records SET payment_status = 'Paid' WHERE record_id = ?",
                (record_id,),
            )
        self.connection.commit()

    def get_unpaid_record(self, plate_number):
        return self.connection.execute(
            """SELECT * FROM parking_records
               WHERE plate_number = ? AND exit_time IS NOT NULL AND payment_status = 'Unpaid'
               ORDER BY record_id DESC LIMIT 1""",
            (plate_number,),
        ).fetchone()

    def create_mpesa_transaction(self, record_id, plate_number, checkout_id,
                                 merchant_id, amount, phone_number, created_at):
        self.connection.execute(
            """INSERT INTO mpesa_transactions
               (record_id, plate_number, checkout_request_id, merchant_request_id,
                amount, phone_number, created_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')""",
            (record_id, plate_number, checkout_id, merchant_id, amount, phone_number, created_at),
        )
        self.connection.commit()

    def get_mpesa_transaction(self, checkout_id):
        return self.connection.execute(
            "SELECT * FROM mpesa_transactions WHERE checkout_request_id = ?",
            (checkout_id,),
        ).fetchone()

    def update_mpesa_transaction(self, checkout_id, status, result_code, description):
        self.connection.execute(
            """UPDATE mpesa_transactions
               SET status = ?, result_code = ?, result_description = ?
               WHERE checkout_request_id = ?""",
            (status, str(result_code), description, checkout_id),
        )
        self.connection.commit()

    def get_all_records(self):
        return self.connection.execute(
            "SELECT * FROM parking_records ORDER BY record_id"
        ).fetchall()

    def close(self):
        self.connection.close()
