# Data Structures and Their Reasons for Use

## 1. Dictionary

Example:

```python
self.slots = {
    1: ParkingSlot(1),
    2: ParkingSlot(2),
}
```

The slot number is the key.

### Why?

A dictionary allows direct access to a slot using its number and is convenient for checking and updating slot status.

---

## 2. Dictionary for Active Vehicles

```python
self.active_vehicles = {}
```

The vehicle registration number is used as the key.

### Why?

Vehicle registration numbers are unique identifiers. A dictionary makes searching for an active vehicle efficient.

---

## 3. Queue

Python's:

```python
from collections import deque
```

is used for vehicles waiting when the car park is full.

### Why?

A queue follows FIFO:

**First In, First Out.**

This is fair for vehicles waiting for a parking space.

---

## 4. List

Database records are converted into a list before sorting and displaying them.

### Why?

Lists are useful for ordered collections of records.

---

## 5. Classes / Objects

The project defines:

- `ParkingSlot`
- `Vehicle`
- `ParkingRecord`

### Why?

Each object groups related data together. This makes the program easier to understand and maintain.

---

## 6. SQLite Tables

The database stores persistent information.

### Why?

Data should not disappear when the Python program closes. SQLite stores the information in a database file.

---

# Summary

| Data structure | Use |
|---|---|
| Dictionary | Parking slots |
| Dictionary | Active vehicles |
| Queue (`deque`) | Vehicles waiting |
| List | Records for display/sorting |
| Classes | Model real-world entities |
| SQLite tables | Persistent storage |
