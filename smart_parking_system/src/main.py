from pathlib import Path
import sys

# Allows `python src/main.py` to work from the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATABASE_NAME, HOURLY_RATE, TOTAL_SLOTS
from src.database import Database
from src.parking_system import ParkingSystem


def show_menu():
    print("\n" + "=" * 45)
    print("       SMART PARKING MANAGEMENT SYSTEM")
    print("=" * 45)
    print("1. Display available slots")
    print("2. Vehicle arrival")
    print("3. Vehicle exit")
    print("4. Process payment / open barrier")
    print("5. Search vehicle")
    print("6. View parking records")
    print("7. View waiting queue")
    print("8. Exit")
    print("=" * 45)


def display_slots(system):
    available = system.display_available_slots()

    print("\nAVAILABLE PARKING SLOTS")
    print("-" * 30)

    if not available:
        print("No parking slots are currently available.")
    else:
        for slot in available:
            print(f"Slot {slot}")

    print(f"\nAvailable slots: {len(available)}")
    print(f"Occupied slots: {TOTAL_SLOTS - len(available)}")


def vehicle_arrival(system):
    print("\nVEHICLE ARRIVAL")
    print("-" * 30)

    plate = input("Enter vehicle registration number: ")
    vehicle_type = input("Enter vehicle type (Car/SUV/etc.): ") or "Car"

    result = system.vehicle_arrival(plate, vehicle_type)

    print("\n" + result["message"] if "message" in result else "")

    if result["success"]:
        print(f"Vehicle: {result['plate_number']}")
        print(f"Assigned slot: {result['slot_number']}")
        print(
            "Arrival time:",
            result["arrival_time"].strftime("%d/%m/%Y %H:%M:%S"),
        )


def vehicle_exit(system):
    print("\nVEHICLE EXIT")
    print("-" * 30)

    plate = input("Enter vehicle registration number: ")

    result = system.vehicle_exit(plate)

    if not result["success"]:
        print(result["message"])
        return

    print(f"\nVehicle: {result['plate_number']}")
    print(f"Slot: {result['slot_number']}")
    print(
        "Arrival:",
        result["arrival_time"].strftime("%d/%m/%Y %H:%M:%S"),
    )
    print(
        "Exit:",
        result["exit_time"].strftime("%d/%m/%Y %H:%M:%S"),
    )
    print(f"Parking duration: {result['duration_hours']} hour(s)")
    print(f"Amount payable: KSh {result['fee']:.2f}")
    print("\nThe slot remains occupied until payment succeeds.")


def process_payment(system):
    print("\nPAYMENT")
    print("-" * 30)

    plate = input("Enter vehicle registration number: ")

    record = system.database.get_unpaid_record(plate)

    if record is None:
        print("No unpaid completed parking record found.")
        return

    required = float(record["fee"])
    print(f"Amount required: KSh {required:.2f}")

    try:
        amount = float(input("Enter amount paid: "))
    except ValueError:
        print("Invalid amount.")
        return

    result = system.process_payment(plate, amount)
    print(result["message"])

    if result["success"]:
        print(f"Change: KSh {result['change']:.2f}")
        print("Barrier status: OPEN")

        if result["next_vehicle"]:
            next_vehicle = result["next_vehicle"]
            print(
                "Next waiting vehicle allocated to slot "
                f"{next_vehicle['slot_number']}."
            )
    else:
        print("Barrier status: CLOSED")


def search_vehicle(system):
    print("\nSEARCH VEHICLE")
    print("-" * 30)

    plate = input("Enter registration number: ")
    vehicle = system.search_vehicle(plate)

    if vehicle is None:
        print("Vehicle not found.")
        return

    print(f"Vehicle: {vehicle.plate_number}")
    print(f"Type: {vehicle.vehicle_type}")
    print(f"Slot: {vehicle.slot_number}")
    print(
        "Arrival:",
        vehicle.arrival_time.strftime("%d/%m/%Y %H:%M:%S"),
    )


def view_records(system):
    print("\nPARKING RECORDS")
    print("-" * 80)

    records = system.get_sorted_records("fee")

    if not records:
        print("No parking records found.")
        return

    for record in records:
        print(
            f"ID: {record['record_id']} | "
            f"Plate: {record['plate_number']} | "
            f"Slot: {record['slot_number']} | "
            f"Duration: {record['duration_hours'] or '-'} | "
            f"Fee: KSh {record['fee']:.2f} | "
            f"Payment: {record['payment_status']}"
        )


def view_queue(system):
    print("\nWAITING QUEUE")
    print("-" * 30)

    if not system.waiting_queue:
        print("The waiting queue is empty.")
        return

    for position, vehicle in enumerate(system.waiting_queue, start=1):
        print(
            f"{position}. {vehicle[0]} ({vehicle[1]})"
        )


def main():
    db = Database(DATABASE_NAME)
    system = ParkingSystem(db)

    print("\nWelcome to the Smart Parking Management System.")
    print(f"Parking capacity: {TOTAL_SLOTS} slots")
    print(f"Example tariff: KSh {HOURLY_RATE:.2f} per started hour")

    try:
        while True:
            show_menu()
            choice = input("Enter your choice: ").strip()

            if choice == "1":
                display_slots(system)
            elif choice == "2":
                vehicle_arrival(system)
            elif choice == "3":
                vehicle_exit(system)
            elif choice == "4":
                process_payment(system)
            elif choice == "5":
                search_vehicle(system)
            elif choice == "6":
                view_records(system)
            elif choice == "7":
                view_queue(system)
            elif choice == "8":
                print("Thank you for using the system.")
                break
            else:
                print("Invalid choice. Please select 1-8.")

    except KeyboardInterrupt:
        print("\nProgram stopped.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
