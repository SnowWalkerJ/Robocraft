import unittest

from robocraft.utils.vector import Vector


class VectorTest(unittest.TestCase):
    def test_sub(self):
        p1 = Vector(7, 8, 9)
        p0 = Vector(3, 2, 4)
        p2 = p1 - p0
        self.assertEqual(p2, Vector(4, 6, 5))

    def test_sub(self):
        p1 = Vector(7, 8, 9)
        d = Vector(1, 0, 0)
        self.assertEqual(p1 * d, p1)
        d = Vector(-1, 0, 0)
        self.assertEqual(p1 * d, Vector(-7, 8, -9))
        d = Vector(0, 0, 1)
        self.assertEqual(p1 * d, Vector(9, 8, -7))
        d = Vector(0, 0, -1)
        self.assertEqual(p1 * d, Vector(-9, 8, 7))
