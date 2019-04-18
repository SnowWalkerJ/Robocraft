from dataclasses import dataclass


@dataclass
class Vector:
    x: int
    y: int
    z: int

    def __neg__(self):
        return Vector(-self.x, -self.y, -self.z)

    def __sub__(self, other):
        return Vector(self.x - other.x,
                      self.y - other.y,
                      self.z - other.z)

    def __add__(self, other):
        return Vector(self.x + other.x,
                      self.y + other.y,
                      self.z + other.z)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        self.z += other.z

    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        self.z -= other.z

    def __eq__(self, other):
        return (self.x == other.x and
                self.y == other.y and
                self.z == other.z)

    def __abs__(self):
        return (self.x * self.x +
                self.y * self.y +
                self.x * self.z) ** 0.5

    def __matmul__(self, other):
        return (self.x * other.x +
                self.y * other.y +
                self.z * other.z)

    def __mul__(self, other):
        """根据other的方向做旋转"""
        x = self.x * other.x - self.z * other.z
        y = self.y
        z = -self.x * other.z + self.z * other.x
        return Vector(x, y, z)
