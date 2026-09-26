import sqlite3
from pathlib import Path


class Database:
    """Handles all persistent SQLite database operations."""

    def __init__(self, db_name: str):
       self.db_name = db_name
       self.connection = sqlite3.connect(
           self.db_name,
           check_same_thread=False
       )
       self.connection.row_factory = sqlite3.Row
       self.create_tables()

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
                payment_status TEXT NOT NULL DEFAULT 'Unpaid'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_time TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)

        self.connection.commit()

    def save_slot(self, slot_number, status):
        self.connection.execute(
            """
            INSERT INTO parking_slots(slot_number, status)
            VALUES (?, ?)
            ON CONFLICT(slot_number)
            DO UPDATE SET status = excluded.status
            """,
            (slot_number, status),
        )
        self.connection.commit()

    def save_vehicle(self, plate_number, vehicle_type):
        self.connection.execute(
            """
            INSERT OR REPLACE INTO vehicles(plate_number, vehicle_type)
            VALUES (?, ?)
            """,
            (plate_number, vehicle_type),
        )
        self.connection.commit()

    def create_parking_record(self, plate_number, slot_number, arrival_time):
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO parking_records
            (plate_number, slot_number, arrival_time, payment_status)
            VALUES (?, ?, ?, 'Unpaid')
            """,
            (plate_number, slot_number, arrival_time.isoformat()),
        )
        self.connection.commit()
        return cursor.lastrowid

    def close_parking_record(
        self, record_id, exit_time, duration_hours, fee
    ):
        self.connection.execute(
            """
            UPDATE parking_records
            SET exit_time = ?, duration_hours = ?, fee = ?
            WHERE record_id = ?
            """,
            (exit_time.isoformat(), duration_hours, fee, record_id),
        )
        self.connection.commit()

    def record_payment(self, record_id, amount, payment_time, status):
        self.connection.execute(
            """
            INSERT INTO payments(record_id, amount, payment_time, status)
            VALUES (?, ?, ?, ?)
            """,
            (record_id, amount, payment_time.isoformat(), status),
        )

        if status == "Paid":
            self.connection.execute(
                """
                UPDATE parking_records
                SET payment_status = 'Paid'
                WHERE record_id = ?
                """,
                (record_id,),
            )

        self.connection.commit()

    def get_unpaid_record(self, plate_number):
        cursor = self.connection.execute(
            """
            SELECT *
            FROM parking_records
            WHERE plate_number = ?
              AND exit_time IS NOT NULL
              AND payment_status = 'Unpaid'
            ORDER BY record_id DESC
            LIMIT 1
            """,
            (plate_number,),
        )
        return cursor.fetchone()

    def get_all_records(self):
        cursor = self.connection.execute(
            """
            SELECT *
            FROM parking_records
            ORDER BY record_id
            """
        )
        return cursor.fetchall()

    def close(self):
        self.connection.close()
