import unittest
from date_converter import convert_bs_to_ad, normalize_location

class TestDateConverter(unittest.TestCase):
    def test_convert_bs_to_ad_valid(self):
        # 2081 Shrawan 1 BS -> 2024-07-16 AD
        ad_str = convert_bs_to_ad(2081, 4, 1)
        self.assertEqual(ad_str, "2024-07-16")
        
    def test_convert_bs_to_ad_invalid(self):
        with self.assertRaises(ValueError):
            convert_bs_to_ad(2081, 13, 1)

    def test_normalize_location(self):
        self.assertEqual(normalize_location("पुरानाे लाइन"), "old_line")
        self.assertEqual(normalize_location("पुरानो लाइन"), "old_line")
        self.assertEqual(normalize_location("old line"), "old_line")
        self.assertEqual(normalize_location("नयाँ लाइन"), "new_line")
        self.assertEqual(normalize_location("नया लाइन"), "new_line")
        self.assertEqual(normalize_location("new line"), "new_line")
        self.assertEqual(normalize_location("Random Pipeline"), "Random Pipeline")
