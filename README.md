# Smart Parking Management System

A Python-based parking management system developed for the Multimedia University of Kenya Data Structures and Algorithms (DSA) Task One.

## Features

The system:
1. Displays available parking slots before entry.
2. Records vehicles when they arrive.
3. Assigns an available parking slot.
4. Records arrival and exit times.
5. Calculates parking duration and parking charges.
6. Calculates VAT on the parking charge.
7. Supports manual/demo payment.
8. Supports Safaricom Daraja 3.0 M-Pesa Express (STK Push).
9. Opens the exit barrier after successful payment.
10. Stores parking, payment, tax and M-Pesa transaction records in SQLite.
11. Uses dictionaries, lists, a FIFO queue, searching and sorting.

## Parking Tariff

The parking charges are:

- Up to 30 minutes: **FREE**
- Up to 2 hours: **KSh 50**
- Up to 4 hours: **KSh 100**
- Up to 6 hours: **KSh 300**
- Over 6 hours: **KSh 500**

The parking charge is used as the subtotal. The application then calculates VAT at the configured rate and adds it to the amount payable.

## Tax

The default VAT rate is 16%. VAT can be enabled or disabled in `src/config.py`.

For example, a KSh 50 parking charge results in:
- Parking charge: KSh 50
- VAT (16%): KSh 8
- Total payable: KSh 58

## M-Pesa

The application includes Safaricom Daraja 3.0 M-Pesa Express STK Push integration.

M-Pesa credentials are read from environment variables. Use `.env.example` as a guide when configuring the application.

The Daraja callback URL must be publicly reachable over HTTPS when testing STK Push callbacks. The application uses the Safaricom sandbox by default.

## Requirements

- Python 3.10 or newer
- Flask
- Requests
- Safaricom Daraja sandbox credentials for M-Pesa testing

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Running the Web Application

```bash
python web/app.py
```

Open the forwarded port 5000 when running the application in Codespaces.

The SQLite database is created automatically.

## Running Tests

```bash
python -m unittest discover -s tests -v
```

## Project Structure

```text
DSA-task1-Y2s1/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── src/
│   ├── config.py
│   ├── models.py
│   ├── database.py
│   ├── parking_system.py
│   ├── tax.py
│   ├── mpesa.py
│   └── main.py
├── web/
│   ├── app.py
│   ├── templates/
│   └── static/
├── docs/
└── tests/
```

## DSA Concepts Used

### Dictionary
Parking slots and active vehicles are stored in dictionaries for direct lookup.

### Queue
Vehicles arriving when all parking slots are occupied are placed in a FIFO queue using `collections.deque`.

### Searching
Vehicles can be searched using their registration numbers.

### Sorting
Parking records can be sorted by duration or amount due.

### Classes and Objects
`Vehicle`, `ParkingSlot`, and `ParkingRecord` group related data.

### Database
SQLite provides persistent storage for parking slots, vehicles, parking records, payments and M-Pesa transactions.

## References

- Safaricom Daraja Developer Portal: https://developer.safaricom.co.ke/
- KRA VAT information: https://www.kra.go.ke/individual/filing-paying/types-of-taxes/value-added-tax
- KRA eTIMS information: https://www.kra.go.ke/business/etims-electronic-tax-invoice-management-system/learn-about-etims/what-is-etims
