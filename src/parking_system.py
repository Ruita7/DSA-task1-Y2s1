from collections import deque
from datetime import datetime
import math

from .config import HOURLY_RATE, TOTAL_SLOTS
from .database import Database
from .models import ParkingRecord, ParkingSlot, Vehicle
from .tax import calculate_tax


class ParkingSystem:
    """Main business logic for the Smart Parking Management System."""

    def __init__(self, database: Database):
        self.database = database
        self.slots = {
            number: ParkingSlot(number)
            for number in range(1, TOTAL_SLOTS + 1)
        }
        self.active_vehicles = {}
        self.waiting_queue = deque()
        self.record_ids = {}

        for slot in self.slots.values():
            self.database.save_slot(slot.slot_number, slot.status)

    def display_available_slots(self):
        return [
            number for number, slot in self.slots.items()
            if slot.status == "Available"
        ]

    def find_first_available_slot(self):
        for number, slot in self.slots.items():
            if slot.status == "Available":
                return number
        return None

    def vehicle_arrival(self, plate_number, vehicle_type="Car"):
        plate_number = plate_number.strip().upper()
        if not plate_number:
            return {"success": False, "message": "Plate number cannot be empty."}
        if plate_number in self.active_vehicles:
            return {"success": False, "message": "This vehicle is already inside the parking lot."}

        slot_number = self.find_first_available_slot()
        if slot_number is None:
            self.waiting_queue.append((plate_number, vehicle_type))
            return {
                "success": False,
                "queued": True,
                "message": "Parking is full. Vehicle was added to the waiting queue.",
            }

        arrival_time = datetime.now()
        self.slots[slot_number].status = "Occupied"
        self.active_vehicles[plate_number] = Vehicle(
            plate_number=plate_number,
            vehicle_type=vehicle_type,
            slot_number=slot_number,
            arrival_time=arrival_time,
        )

        self.database.save_slot(slot_number, "Occupied")
        self.database.save_vehicle(plate_number, vehicle_type)
        record_id = self.database.create_parking_record(
            plate_number, slot_number, arrival_time
        )
        self.record_ids[plate_number] = record_id

        return {
            "success": True,
            "plate_number": plate_number,
            "slot_number": slot_number,
            "arrival_time": arrival_time,
        }

    @staticmethod
    def calculate_duration(arrival_time, exit_time):
        seconds = (exit_time - arrival_time).total_seconds()
        if seconds <= 30 * 60:
            return 0
        return math.ceil(seconds / 3600)

    @staticmethod
    def calculate_fee(duration_hours):
        if duration_hours <= 0:
            return 0.0
        if duration_hours <= 2:
            return 50.0
        if duration_hours <= 4:
            return 100.0
        if duration_hours <= 6:
            return 300.0
        return 500.0

    def vehicle_exit(self, plate_number):
        plate_number = plate_number.strip().upper()
        vehicle = self.active_vehicles.get(plate_number)
        if vehicle is None:
            return {"success": False, "message": "Vehicle not found in the active parking records."}

        exit_time = datetime.now()
        duration_hours = self.calculate_duration(vehicle.arrival_time, exit_time)
        subtotal = self.calculate_fee(duration_hours)
        tax = calculate_tax(subtotal)
        record_id = self.record_ids[plate_number]

        self.database.close_parking_record(
            record_id,
            exit_time,
            duration_hours,
            subtotal,
            tax.tax_amount,
            tax.total,
        )

        return {
            "success": True,
            "record_id": record_id,
            "plate_number": plate_number,
            "slot_number": vehicle.slot_number,
            "arrival_time": vehicle.arrival_time,
            "exit_time": exit_time,
            "duration_hours": duration_hours,
            "fee": subtotal,
            "tax_amount": tax.tax_amount,
            "total_due": tax.total,
        }

    def process_payment(self, plate_number, amount):
        plate_number = plate_number.strip().upper()
        record = self.database.get_unpaid_record(plate_number)
        if record is None:
            return {"success": False, "barrier_open": False, "message": "No unpaid completed parking record found."}

        required = float(record["total_due"])
        if amount < required:
            return {
                "success": False,
                "barrier_open": False,
                "message": f"Insufficient payment. Required KSh {required:.2f}.",
            }

        payment_time = datetime.now()
        self.database.record_payment(record["record_id"], amount, payment_time, "Paid")
        return self._complete_paid_exit(plate_number, amount, required)

    def _complete_paid_exit(self, plate_number, amount, required):
        vehicle = self.active_vehicles.pop(plate_number, None)
        if vehicle is not None:
            self.slots[vehicle.slot_number].status = "Available"
            self.database.save_slot(vehicle.slot_number, "Available")
            self.record_ids.pop(plate_number, None)

        next_vehicle = self.allocate_next_waiting_vehicle()
        return {
            "success": True,
            "barrier_open": True,
            "message": "Payment successful. Barrier opened.",
            "change": amount - required,
            "next_vehicle": next_vehicle,
        }

    def complete_mpesa_payment(self, plate_number, amount, transaction_reference):
        """Record a successful Daraja callback and open the barrier."""
        plate_number = plate_number.strip().upper()
        record = self.database.get_unpaid_record(plate_number)
        if record is None:
            return {"success": False, "message": "No unpaid record found."}

        required = float(record["total_due"])
        if float(amount) < required:
            return {"success": False, "message": "M-Pesa amount is below the amount due."}

        self.database.record_payment(
            record["record_id"], float(amount), datetime.now(), "Paid", transaction_reference
        )
        return self._complete_paid_exit(plate_number, float(amount), required)

    def allocate_next_waiting_vehicle(self):
        if not self.waiting_queue:
            return None
        slot_number = self.find_first_available_slot()
        if slot_number is None:
            return None
        plate_number, vehicle_type = self.waiting_queue.popleft()
        return self.vehicle_arrival(plate_number, vehicle_type)

    def search_vehicle(self, plate_number):
        return self.active_vehicles.get(plate_number.strip().upper())

    def get_sorted_records(self, sort_by="fee"):
        records = [dict(row) for row in self.database.get_all_records()]
        if sort_by == "duration":
            records.sort(key=lambda record: record["duration_hours"] or 0, reverse=True)
        else:
            records.sort(key=lambda record: record["total_due"] or 0, reverse=True)
        return records
