import os
import tempfile
import unittest

from src.database import Database
from src.parking_system import ParkingSystem
from src.tax import calculate_tax


class ParkingSystemTests(unittest.TestCase):

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = Database(self.temp_db.name)
        self.system = ParkingSystem(self.db)

    def tearDown(self):
        self.db.close()
        os.unlink(self.temp_db.name)

    def test_initial_slots_are_available(self):
        self.assertEqual(len(self.system.display_available_slots()), 10)

    def test_vehicle_is_assigned_a_slot(self):
        result = self.system.vehicle_arrival("KDA123A", "Car")
        self.assertTrue(result["success"])
        self.assertEqual(result["slot_number"], 1)
        self.assertEqual(len(self.system.display_available_slots()), 9)

    def test_duplicate_vehicle_is_rejected(self):
        self.system.vehicle_arrival("KDA123A", "Car")
        result = self.system.vehicle_arrival("KDA123A", "Car")
        self.assertFalse(result["success"])
        self.assertIn("already inside", result["message"])

    def test_fee_calculation(self):
        self.assertEqual(self.system.calculate_fee(1), 50.0)
        self.assertEqual(self.system.calculate_fee(3), 150.0)

    def test_vat_calculation(self):
        tax = calculate_tax(50.0)
        self.assertEqual(tax.subtotal, 50.0)
        self.assertEqual(tax.tax_amount, 8.0)
        self.assertEqual(tax.total, 58.0)


if __name__ == "__main__":
    unittest.main()
