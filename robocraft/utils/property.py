from numbers import Number
from typing import Union, Dict

from .typecheck import type_check, overload


class Property:
    @overload
    def __init__(self, value: Dict[str, Number]):
        self.data = value.copy()
        if "default" not in self.data:
            self.data['default'] = 0

    @__init__.register
    def _(self, value: Number):
        self.data = {'default': value}

    def __getattr__(self, attr):
        if attr == "data":
            return super().__getattr__(attr)
        if attr in self.data:
            return self.data[attr]
        else:
            return self.data['default']

    def __setattr__(self, attr, value):
        if attr == "data":
            return super().__setattr__(attr, value)
        self.data[attr] = value

    def __iadd__(self, other):
        if isinstance(other, Number):
            for key in self.data.keys():
                self.data[key] += other
        elif isinstance(other, Property):
            for key in other.keys():
                value = getattr(other, key)
                if key in self.data:
                    self.data[key] += value
                else:
                    self.data[key] = self.data['default'] + value

    def __add__(self, other):
        data = self.data.copy()
        if isinstance(other, Number):
            for key in data.keys():
                data[key] += other
        elif isinstance(other, Property):
            for key in other.keys():
                value = getattr(other, key)
                if key in data:
                    data[key] += value
                else:
                    data[key] = data['default'] + value
        return Property(data)

    def __mul__(self, other):
        data = self.data.copy()
        if isinstance(other, Number):
            for key in data.keys():
                data[key] *= other
        elif isinstance(other, Property):
            for key in other.keys():
                value = getattr(other, key)
                if key in data:
                    data[key] *= value
                else:
                    data[key] = data['default'] * value
        return Property(data)

    def keys(self):
        return self.data.keys()

    def __repr__(self):
        if len(self.data) == 1:
            return repr(self.data['default'])
        else:
            return repr(self.data)
