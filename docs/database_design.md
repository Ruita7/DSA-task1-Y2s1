# Dynamic Database Design

The project uses SQLite because it is included in Python's standard library and does not require a separate database server.

## Entity 1: parking_slots

| Field | Type | Description |
|---|---|---|
| slot_number | INTEGER | Primary key and slot number |
| status | TEXT | Available or Occupied |

## Entity 2: vehicles

| Field | Type | Description |
|---|---|---|
| plate_number | TEXT | Primary key / vehicle identifier |
| vehicle_type | TEXT | Car, SUV, etc. |

## Entity 3: parking_records

| Field | Type | Description |
|---|---|---|
| record_id | INTEGER | Primary key |
| plate_number | TEXT | Vehicle identifier |
| slot_number | INTEGER | Parking slot |
| arrival_time | TEXT | Time vehicle entered |
| exit_time | TEXT | Time vehicle left |
| duration_hours | INTEGER | Billable duration |
| fee | REAL | Amount payable |
| payment_status | TEXT | Paid or Unpaid |

## Entity 4: payments

| Field | Type | Description |
|---|---|---|
| payment_id | INTEGER | Primary key |
| record_id | INTEGER | Parking record being paid |
| amount | REAL | Amount received |
| payment_time | TEXT | Payment timestamp |
| status | TEXT | Paid/failed status |

## Relationships

```text
VEHICLES
   |
   | plate_number
   v
PARKING_RECORDS
   |
   | record_id
   v
PAYMENTS

PARKING_SLOTS
   |
   | slot_number
   v
PARKING_RECORDS
```

The database is dynamic because records can be inserted and updated while the program is running.

## Database operations used

- `CREATE TABLE IF NOT EXISTS`
- `INSERT`
- `UPDATE`
- `SELECT`

Parameterized SQL (`?`) is used to avoid constructing SQL statements by string concatenation.
