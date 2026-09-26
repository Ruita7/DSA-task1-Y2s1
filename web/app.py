from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATABASE_NAME, HOURLY_RATE, TOTAL_SLOTS
from src.database import Database
from src.parking_system import ParkingSystem

app = Flask(__name__)
app.secret_key = "smart-parking-demo-key"

db = Database(DATABASE_NAME)
system = ParkingSystem(db)

def dashboard_data():
    available = system.display_available_slots()
    return {
        "slots": [{"number": n, "status": s.status} for n, s in system.slots.items()],
        "available_count": len(available),
        "occupied_count": TOTAL_SLOTS - len(available),
        "capacity": TOTAL_SLOTS,
        "hourly_rate": HOURLY_RATE,
        "records": system.get_sorted_records("fee"),
        "queue": list(system.waiting_queue),
    }

@app.route("/")
def index():
    return render_template("index.html", **dashboard_data())

@app.post("/arrival")
def arrival():
    result = system.vehicle_arrival(
        request.form.get("plate_number", ""),
        request.form.get("vehicle_type", "Car"),
    )
    if result["success"]:
        flash(f"{result['plate_number']} assigned to Slot {result['slot_number']}.", "success")
    else:
        flash(result["message"], "warning" if result.get("queued") else "error")
    return redirect(url_for("index"))

@app.post("/exit")
def exit_vehicle():
    result = system.vehicle_exit(request.form.get("plate_number", ""))
    if result["success"]:
        flash(f"{result['plate_number']} owes KSh {result['fee']:.2f} for {result['duration_hours']} hour(s).", "success")
    else:
        flash(result["message"], "error")
    return redirect(url_for("index"))

@app.post("/payment")
def payment():
    plate = request.form.get("plate_number", "")
    try:
        amount = float(request.form.get("amount", ""))
    except ValueError:
        flash("Please enter a valid payment amount.", "error")
        return redirect(url_for("index"))
    result = system.process_payment(plate, amount)
    if result["success"]:
        message = f"Payment successful. Barrier OPEN. Change: KSh {result['change']:.2f}."
        if result.get("next_vehicle"):
            n = result["next_vehicle"]
            message += f" {n['plate_number']} from the waiting queue was assigned Slot {n['slot_number']}."
        flash(message, "success")
    else:
        flash(result["message"] + " Barrier CLOSED.", "error")
    return redirect(url_for("index"))

@app.get("/search")
def search():
    plate = request.args.get("plate_number", "")
    return render_template("search.html", vehicle=system.search_vehicle(plate), plate=plate.upper(), **dashboard_data())

@app.get("/records")
def records():
    sort_by = request.args.get("sort", "fee")
    if sort_by not in ("fee", "duration"):
        sort_by = "fee"
    return render_template("records.html", **dashboard_data(), sort_by=sort_by)

@app.get("/health")
def health():
    return {"status": "ok", "application": "Smart Parking Management System"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
