from datetime import datetime
from pathlib import Path
import sys

from flask import Flask, jsonify, render_template, request, redirect, url_for, flash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATABASE_NAME, HOURLY_RATE, TOTAL_SLOTS, VAT_RATE, VAT_ENABLED
from src.database import Database
from src.mpesa import MpesaError, initiate_stk_push
from src.parking_system import ParkingSystem

app = Flask(__name__)
app.secret_key = "smart-parking-demo-key"

import os

MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
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
        "vat_enabled": VAT_ENABLED,
        "vat_rate": VAT_RATE,
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
        flash(
            f"{result['plate_number']}: KSh {result['fee']:.2f} parking + "
            f"KSh {result['tax_amount']:.2f} tax = KSh {result['total_due']:.2f} due.",
            "success",
        )
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


@app.post("/mpesa/pay")
def mpesa_pay():
    plate = request.form.get("plate_number", "").strip().upper()
    phone = request.form.get("phone_number", "").strip()
    record = db.get_unpaid_record(plate)

    if record is None:
        flash("Calculate the parking fee first. No unpaid completed record was found.", "error")
        return redirect(url_for("index"))

    amount = float(record["total_due"])
    try:
        response = initiate_stk_push(phone, amount, plate)
        db.create_mpesa_transaction(
            record["record_id"],
            plate,
            response["CheckoutRequestID"],
            response.get("MerchantRequestID"),
            amount,
            phone,
            datetime.now().isoformat(),
        )
        flash(
            f"M-Pesa prompt sent to {phone}. Enter your M-Pesa PIN on the phone to complete payment.",
            "success",
        )
    except (MpesaError, KeyError, ValueError) as exc:
        flash(f"M-Pesa could not be started: {exc}", "error")
    return redirect(url_for("index"))


@app.post("/mpesa/callback")
def mpesa_callback():
    """Daraja callback endpoint. Must be publicly reachable over HTTPS in production."""
    data = request.get_json(silent=True) or {}
    callback = data.get("Body", {}).get("stkCallback", {})
    checkout_id = callback.get("CheckoutRequestID")
    result_code = callback.get("ResultCode")
    description = callback.get("ResultDesc", "")

    if not checkout_id:
        return jsonify({"ResultCode": 1, "ResultDesc": "Missing CheckoutRequestID"}), 400

    transaction = db.get_mpesa_transaction(checkout_id)
    if transaction is None:
        return jsonify({"ResultCode": 1, "ResultDesc": "Transaction not found"}), 404

    if result_code != 0:
        db.update_mpesa_transaction(checkout_id, "Failed", result_code, description)
        return jsonify({"ResultCode": 0, "ResultDesc": "Callback received"})

    metadata = callback.get("CallbackMetadata", {}).get("Item", [])
    values = {item.get("Name"): item.get("Value") for item in metadata if item.get("Name")}
    mpesa_amount = float(values.get("Amount", transaction["amount"]))
    receipt = values.get("MpesaReceiptNumber", "")

    db.update_mpesa_transaction(checkout_id, "Paid", result_code, description)
    result = system.complete_mpesa_payment(
        transaction["plate_number"], mpesa_amount, receipt
    )
    if not result["success"]:
        return jsonify({"ResultCode": 1, "ResultDesc": result["message"]}), 400

    return jsonify({"ResultCode": 0, "ResultDesc": "Callback received"})


@app.get("/search")
def search():
    plate = request.args.get("plate_number", "")
    return render_template(
        "search.html",
        vehicle=system.search_vehicle(plate),
        plate=plate.upper(),
        **dashboard_data(),
    )


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
