# Smart Parking Management System

A beginner-friendly Python implementation of the Multimedia University of Kenya Data Structures and Algorithms (DSA) Task One.

## Problem addressed

The system:
1. Displays available parking slots before entry.
2. Records vehicles when they arrive.
3. Assigns an available parking slot.
4. Records arrival and exit times.
5. Calculates parking duration.
6. Calculates the parking charge.
7. Calculates configurable Kenyan VAT.
8. Supports manual/demo payment.
9. Supports Safaricom Daraja 3.0 M-Pesa Express (STK Push) when Daraja credentials and a public HTTPS callback are configured.
10. Opens the exit barrier only after successful payment.
11. Keeps parking, tax, payment and M-Pesa transaction records in SQLite.
12. Uses DSA concepts such as dictionaries, lists, a FIFO queue, searching, and sorting.

## Taxation

The project includes a configurable VAT calculator. The default configuration uses the 16% general VAT rate published by KRA for taxable supplies. Whether VAT should actually be charged depends on the parking operator's KRA tax status and the tax treatment of the service.

The application calculates and displays the tax; it does **not** claim to be an eTIMS tax-invoice or automatic KRA filing system. A production deployment would require the appropriate KRA/eTIMS compliance integration and configuration.

Change `VAT_ENABLED` or `VAT_RATE` in `src/config.py` if the client/lecturer specifies different treatment.

## M-Pesa Daraja

The project includes a Safaricom Daraja 3.0 M-Pesa Express STK Push integration.

Credentials are read from environment variables and are not stored in GitHub. Use `.env.example` as a template and add real credentials only to your Codespaces/local environment.

The Daraja callback URL must be publicly reachable over HTTPS for real STK Push callbacks. GitHub Codespaces can be used for development/testing, but a stable HTTPS endpoint is recommended for production.

The integration targets the Daraja sandbox by default.

## Requirements

- Python 3.10 or newer
- Flask
- Requests
- Safaricom Daraja sandbox credentials for M-Pesa testing

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the web application

```bash
python web/app.py
```

Then open the forwarded port 5000 in Codespaces.

The SQLite database `parking.db` is created automatically. Existing databases are upgraded with the new tax and M-Pesa transaction columns/tables.

## Test the DSA code

```bash
python -m unittest discover -s tests -v
```

## Project structure

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

## Important project assumptions

The original DSA assignment does not specify a parking tariff, so the project uses a configurable example rate of **KSh 50 per started hour**. The tax setting is also configurable.

## Main DSA concepts

### Dictionary
Parking slots and active vehicles are stored in dictionaries for direct lookup.

### Queue
Vehicles that arrive when all slots are occupied are placed in a FIFO queue using `collections.deque`.

### Searching
Vehicles are searched using their registration numbers.

### Sorting
Parking records can be sorted by duration or amount due.

### Classes / objects
`Vehicle`, `ParkingSlot`, and `ParkingRecord` group related data together.

### Database
SQLite provides persistent storage for parking slots, vehicles, parking records, payments and M-Pesa transaction state.

## Official references

- Safaricom Daraja Developer Portal: https://developer.safaricom.co.ke/
- KRA VAT information: https://www.kra.go.ke/individual/filing-paying/types-of-taxes/value-added-tax
- KRA eTIMS information: https://www.kra.go.ke/business/etims-electronic-tax-invoice-management-system/learn-about-etims/what-is-etims
