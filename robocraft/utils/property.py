import inspect
from numbers import Real, Real

from .typecheck import overload


class PropertyMeta(type):
    def __new__(cls, name, bases, attrs):
        if '__annotations__' in attrs and '__init__' in attrs:
            attrs['__init__'].__annotations__ = attrs['__annotations__']
        return super().__new__(cls, name, bases, attrs)


class PropertyBase(metaclass=PropertyMeta):
    @overload
    def __init__(self, *args, **kwargs):
        params = [
            inspect.Parameter(key, inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=_type, default=_type())
            for key, _type in self.__annotations__.items()
        ]
        signature = inspect.Signature(params)

        params = signature.bind(*args, **kwargs)
        params.apply_defaults()
        for key, value in params.arguments.items():
            _type = self.__annotations__[key]
            if issubclass(_type, PropertyBase):
                if isinstance(value, dict):
                    value = _type(**value)
                elif isinstance(value, PropertyBase):
                    kwargs = {key: getattr(value, key) for key in value.__annotations__}
                    value = _type(**kwargs)
                else:
                    value = _type(value)
            setattr(self, key, value)

    def __repr__(self):
        data = " ".join(f"{key}={repr(getattr(self, key))}" for key in self.__annotations__)
        return f"<{self.__class__.__qualname__} {data}>"

    @overload
    def __add__(self, other):
        result = self.__class__()
        for key in other.__annotations__.keys():
            setattr(result, key, getattr(self, key) + getattr(other, key))
        return result

    @__add__.register
    def __add__(self, other: Real):
        result = self.__class__()
        for key in self.__annotations__.keys():
            setattr(result, key, getattr(self, key) + other)
        return result

    @overload
    def __sub__(self, other):
        result = self.__class__()
        for key in other.__annotations__.keys():
            setattr(result, key, getattr(self, key) - getattr(other, key))
        return result

    @__sub__.register
    def __sub__(self, other: Real):
        result = self.__class__()
        for key in self.__annotations__.keys():
            setattr(result, key, getattr(self, key) - other)
        return result

    @overload
    def __mul__(self, other):
        result = self.__class__()
        for key in self.__annotations__.keys():
            if hasattr(other, key):
                setattr(result, key, getattr(self, key) * getattr(other, key))
            else:
                setattr(result, key, getattr(self, key))
        return result

    @__mul__.register
    def __mul__(self, other: Real):
        result = self.__class__()
        for key in self.__annotations__.keys():
            setattr(result, key, getattr(self, key) * other)
        return result

    @overload
    def __truediv__(self, other):
        result = self.__class__()
        for key in other.__annotations__.keys():
            setattr(result, key, getattr(self, key) / getattr(other, key))
        return result

    @__truediv__.register
    def __truediv__(self, other: Real):
        result = self.__class__()
        for key in self.__annotations__.keys():
            setattr(result, key, getattr(self, key) / other)
        return result

    def keys(self):
        return self.__annotations__.keys()

    def __setattr__(self, key, value):
        if key in self.__annotations__:
            _type = self.__annotations__[key]
            assert isinstance(value, _type)
        super().__setattr__(key, value)


class PureProperty(PropertyBase):
    @PropertyBase.__init__.register
    def __init__(self, value: Real):
        for key in self.__annotations__.keys():
            setattr(self, key, value)


class AttackProperty(PureProperty):
    normal: float
    back: float


class SpeedProperty(PureProperty):
    senseForward: float
    senseSurroundings: float
    rotate: float
    moveForward: float
    moveBackward: float
    moveUpward: float
    moveDownward: float
    attack: float


class CapacityProperty(PureProperty):
    weight: int
    space: int


class RobotProperty(PropertyBase):
    hp: float
    mp: float
    attack: AttackProperty
    defense: AttackProperty
    speed: SpeedProperty
    senseRadius: float
    senseDistance: float
    capacity: CapacityProperty


class ComponentProperty(PropertyBase):
    attack: AttackProperty
    defense: AttackProperty
    speed: SpeedProperty
    costs: CapacityProperty



CapacityProperty(100, 100)