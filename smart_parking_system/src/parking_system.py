from collections import deque
from datetime import datetime
import math

from .config import HOURLY_RATE, TOTAL_SLOTS
from .database import Database
from .models import ParkingRecord, ParkingSlot, Vehicle


class ParkingSystem:
    """
    Main business logic for the Smart Parking Management System.

    Data structures used:
    - Dictionary for parking slots.
    - Dictionary for active vehicles.
    - deque for the waiting queue.
    - List for returned/displayed records.
    """

    def __init__(self, database: Database):
        self.database = database

        self.slots = {
            number: ParkingSlot(number)
            for number in range(1, TOTAL_SLOTS + 1)
        }

        self.active_vehicles = {}
        self.waiting_queue = deque()
        self.record_ids = {}

        # Save initial slot state to the database.
        for slot in self.slots.values():
            self.database.save_slot(slot.slot_number, slot.status)

    def display_available_slots(self):
        """Return a list of currently available slot numbers."""
        return [
            number
            for number, slot in self.slots.items()
            if slot.status == "Available"
        ]

    def find_first_available_slot(self):
        """Linear search for the first available slot."""
        for number, slot in self.slots.items():
            if slot.status == "Available":
                return number
        return None

    def vehicle_arrival(self, plate_number, vehicle_type="Car"):
        """
        Register a vehicle and allocate a slot.

        If all slots are occupied, add the vehicle to the FIFO waiting queue.
        """
        plate_number = plate_number.strip().upper()

        if not plate_number:
            return {"success": False, "message": "Plate number cannot be empty."}

        if plate_number in self.active_vehicles:
            return {
                "success": False,
                "message": "This vehicle is already inside the parking lot.",
            }

        slot_number = self.find_first_available_slot()

        if slot_number is None:
            self.waiting_queue.append((plate_number, vehicle_type))
            return {
                "success": False,
                "queued": True,
                "message": (
                    "Parking is full. Vehicle was added to the waiting queue."
                ),
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
        """
        Calculate billable hours.

        A started hour counts as one hour.
        Minimum charge is therefore one hour.
        """
        seconds = (exit_time - arrival_time).total_seconds()
        hours = max(1, math.ceil(seconds / 3600))
        return hours

    @staticmethod
    def calculate_fee(duration_hours):
        return duration_hours * HOURLY_RATE

    def vehicle_exit(self, plate_number):
        """Record exit and calculate the fee for an active vehicle."""
        plate_number = plate_number.strip().upper()

        vehicle = self.active_vehicles.get(plate_number)

        if vehicle is None:
            return {
                "success": False,
                "message": "Vehicle not found in the active parking records.",
            }

        exit_time = datetime.now()
        duration_hours = self.calculate_duration(
            vehicle.arrival_time, exit_time
        )
        fee = self.calculate_fee(duration_hours)

        record_id = self.record_ids[plate_number]

        self.database.close_parking_record(
            record_id, exit_time, duration_hours, fee
        )

        # The slot is kept occupied until payment succeeds.
        return {
            "success": True,
            "record_id": record_id,
            "plate_number": plate_number,
            "slot_number": vehicle.slot_number,
            "arrival_time": vehicle.arrival_time,
            "exit_time": exit_time,
            "duration_hours": duration_hours,
            "fee": fee,
        }

    def process_payment(self, plate_number, amount):
        """
        Process a simulated payment.

        The barrier opens only if the payment covers the fee.
        """
        plate_number = plate_number.strip().upper()
        record = self.database.get_unpaid_record(plate_number)

        if record is None:
            return {
                "success": False,
                "barrier_open": False,
                "message": "No unpaid completed parking record found.",
            }

        required = float(record["fee"])

        if amount < required:
            return {
                "success": False,
                "barrier_open": False,
                "message": (
                    f"Insufficient payment. Required KSh {required:.2f}."
                ),
            }

        payment_time = datetime.now()

        self.database.record_payment(
            record["record_id"],
            amount,
            payment_time,
            "Paid",
        )

        # Free the slot only after successful payment.
        vehicle = self.active_vehicles.pop(plate_number, None)

        if vehicle is not None:
            self.slots[vehicle.slot_number].status = "Available"
            self.database.save_slot(vehicle.slot_number, "Available")
            self.record_ids.pop(plate_number, None)

        # If a queue exists, the first waiting vehicle can be allocated.
        next_vehicle = self.allocate_next_waiting_vehicle()

        return {
            "success": True,
            "barrier_open": True,
            "message": "Payment successful. Barrier opened.",
            "change": amount - required,
            "next_vehicle": next_vehicle,
        }

    def allocate_next_waiting_vehicle(self):
        """
        FIFO queue operation.

        The first vehicle waiting is allocated the newly available slot.
        """
        if not self.waiting_queue:
            return None

        slot_number = self.find_first_available_slot()

        if slot_number is None:
            return None

        plate_number, vehicle_type = self.waiting_queue.popleft()

        result = self.vehicle_arrival(plate_number, vehicle_type)
        return result

    def search_vehicle(self, plate_number):
        """Search the active vehicle dictionary by registration number."""
        plate_number = plate_number.strip().upper()
        return self.active_vehicles.get(plate_number)

    def get_sorted_records(self, sort_by="fee"):
        """Return database records sorted by fee or duration."""
        records = [dict(row) for row in self.database.get_all_records()]

        if sort_by == "duration":
            records.sort(
                key=lambda record: record["duration_hours"] or 0,
                reverse=True,
            )
        else:
            records.sort(
                key=lambda record: record["fee"] or 0,
                reverse=True,
            )

        return records
