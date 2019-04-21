import unittest
from robocraft.utils.property import *


class PropertyTest(unittest.TestCase):
    def test_init_number(self):
        p = AttackProperty(1.0)
        self.assertEqual(p.normal, 1.0)
        self.assertEqual(p.back, 1.0)

    def test_init_dict(self):
        p = AttackProperty(normal=1.0, back=2.0)
        self.assertEqual(p.normal, 1.0)
        self.assertEqual(p.back, 2.0)

    def test_add_number(self):
        p = AttackProperty(1.0)
        p = p + 1.0
        self.assertEqual(p.normal, 2.0)

    def test_add_property(self):
        p1 = AttackProperty(1.0)
        p2 = AttackProperty(back=0.5)
        p = p1 + p2
        self.assertEqual(p.normal, 1.0)
        self.assertEqual(p.back, 1.5)

    def test_compound(self):
        p = ComponentProperty(attack=1.0, defense=0.0, speed=0.0, costs=0.0)
        self.assertEqual(p.attack.normal, 1.0)
        self.assertEqual(p.attack.back, 1.0)
