# Smart Parking Management System

A beginner-friendly Python implementation of the Multimedia University of Kenya Data Structures and Algorithms (DSA) Task One.

## Problem addressed

The system:
1. Displays available parking slots before entry.
2. Records vehicles when they arrive.
3. Assigns an available parking slot.
4. Records arrival and exit times.
5. Calculates parking duration.
6. Calculates the parking fee.
7. Records payment.
8. Opens the exit barrier only after successful payment.
9. Keeps parking and payment records in a dynamic SQLite database.
10. Uses DSA concepts such as dictionaries, lists, a queue, searching, and sorting.

## Important assumption

The assignment does not specify a parking tariff. This project therefore uses a configurable rate of **KSh 50 per started hour**, with a minimum charge of one hour.

Change `HOURLY_RATE` in `src/config.py` if your lecturer/client gives a different rate.

## Requirements

- Python 3.10 or newer
- No external Python packages are required.

## Run the program

From the project folder:

```bash
python src/main.py
```

The SQLite database `parking.db` is created automatically the first time the program runs.

## Project structure

```text
smart_parking_system/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── database.py
│   ├── parking_system.py
│   └── main.py
├── docs/
│   ├── algorithms.md
│   ├── data_structures.md
│   └── database_design.md
└── tests/
    └── test_parking_system.py
```

## Main DSA concepts

### Dictionary
Parking slots are stored as a dictionary:
- key = slot number
- value = `ParkingSlot` object

This gives fast direct access to a slot.

### Queue
Vehicles that arrive when all slots are occupied are placed in a FIFO queue using `collections.deque`.

FIFO means **First In, First Out**.

### Searching
A vehicle is searched using its registration number.

### Sorting
Parking records can be sorted by duration or fee.

### Classes / objects
`Vehicle`, `ParkingSlot`, and `ParkingRecord` group related data together.

### Database
SQLite provides persistent storage for vehicles, slots, parking records, and payments.

## Testing

Run:

```bash
python -m unittest discover -s tests -v
```

## GitHub

After creating a GitHub repository:

```bash
git init
git add .
git commit -m "Initial smart parking system"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with the URL of your own GitHub repository.

Do not commit the generated `parking.db` file if you want GitHub to contain only the source project. The database file is ignored by `.gitignore`.
