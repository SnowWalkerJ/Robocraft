import unittest
from robocraft.utils.property import Property


class PropertyTest(unittest.TestCase):
    def test_init_number(self):
        p = Property(1.0)
        self.assertListEqual(list(p.keys()), ['default'])
        self.assertEqual(p.default, 1.0)

    def test_init_dict(self):
        p = Property({"back": 1.0, "default": 2.0})
        self.assertEqual(p.default, 2.0)
        self.assertEqual(p.back, 1.0)

    def test_add_number(self):
        p = Property(1.0)
        p = p + 1.0
        self.assertEqual(p.default, 2.0)

    def test_add_property(self):
        p1 = Property(1.0)
        p2 = Property({"back": 0.5})
        p = p1 + p2
        self.assertEqual(p.default, 1.0)
        self.assertEqual(p.back, 1.5)
