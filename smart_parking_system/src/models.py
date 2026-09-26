from dataclasses import dataclass
from datetime import datetime


@dataclass
class ParkingSlot:
    slot_number: int
    status: str = "Available"


@dataclass
class Vehicle:
    plate_number: str
    vehicle_type: str
    slot_number: int
    arrival_time: datetime


@dataclass
class ParkingRecord:
    record_id: int | None
    plate_number: str
    slot_number: int
    arrival_time: datetime
    exit_time: datetime | None
    duration_hours: int | None
    fee: float
    payment_status: str
