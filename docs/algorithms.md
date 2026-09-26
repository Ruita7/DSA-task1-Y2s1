# Algorithms

## 1. Display Available Slots

### Pseudocode

```text
START
available = 0

FOR each slot in parking_slots
    IF slot.status = "Available"
        DISPLAY slot number
        available = available + 1
    END IF
END FOR

DISPLAY available
END
```

### Complexity

If there are `n` slots, every slot may be checked once.

Time complexity: **O(n)**.

---

## 2. Find First Available Slot

```text
START
FOR each slot from first to last
    IF slot is Available
        RETURN slot number
    END IF
END FOR

RETURN None
END
```

Time complexity: **O(n)** in the worst case.

---

## 3. Vehicle Arrival

```text
START
Read vehicle registration

IF registration already exists among active vehicles
    DISPLAY error
    STOP
END IF

Find first available slot

IF no slot exists
    Add vehicle to FIFO waiting queue
    STOP
END IF

Mark selected slot as Occupied
Record vehicle information
Record arrival time
Save record in database

DISPLAY assigned slot
END
```

---

## 4. Vehicle Exit

```text
START
Read vehicle registration

Search active vehicles

IF vehicle is not found
    DISPLAY error
    STOP
END IF

Record exit time
Calculate elapsed time
Round up to the next started hour
Calculate fee
Save exit and fee to database

KEEP SLOT OCCUPIED UNTIL PAYMENT
DISPLAY amount payable
END
```

---

## 5. Fee Calculation

For this demonstration:

```text
fee = billable_hours × hourly_rate
```

A minimum of one hour is charged.

Example:

```text
Duration = 2 hours 10 minutes
Billable hours = 3
Rate = KSh 50/hour

Fee = 3 × 50
Fee = KSh 150
```

The rate is configurable because the assignment does not specify an official tariff.

---

## 6. Payment and Barrier

```text
START
Find unpaid completed record

IF no record exists
    KEEP barrier closed
    STOP
END IF

IF amount paid < required fee
    KEEP barrier closed
    DISPLAY insufficient payment
ELSE
    Record payment
    Free parking slot
    Open barrier
    Serve first vehicle in waiting queue if one exists
END IF

END
```

---

## 7. Search Vehicle

The active vehicle dictionary is searched using the vehicle registration number.

Average dictionary lookup is approximately **O(1)**.

---

## 8. Waiting Queue

Vehicles that arrive while the car park is full are placed at the rear of a queue.

When a slot becomes free, the vehicle at the front is served first.

This follows:

**FIFO — First In, First Out.**

Adding and removing from a `deque` at the ends is **O(1)**.

---

## 9. Sorting

Parking records can be sorted by:
- fee
- duration

Python's built-in sorting is based on Timsort and has average/worst-case time complexity of **O(n log n)**.
