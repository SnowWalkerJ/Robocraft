"""
Usage
=====

type_check
----------

..  code-block::python

    from type_check import type_check

    @type_check()
    def fn(a: int, b: str):
        ...

    @type_check(True)
    def fn2(a: List[int]):
        ...

    fn(1, "a")    # OK
    fn(1.0, "b")  # Raises TypeError
    fn2([1,2,3])  # OK
    fn2([])       # OK
    fn2([1.0])    # Raises TypeError

overload
--------

..  code-block::python

    from type_check import overload
    
    @overload
    def fn(a):
        raise TypeError
        
    @fn.register
    def _(a: int):
        print(a, "is int")
        
    @fn.register
    def _(a: float):
        print(a, "is float")
        
    fn(1)            # 1 is int
    fn(2.0)          # 2.0 is float

"""
from functools import wraps
from inspect import signature, _empty
import sys
from typing import List, Tuple, Dict, Any, Union


CHECK_ELEMENTS = False
# Turn this to True to check the type of elements.
# Note this will seriously affect performance.


def _check_is_complex_type(type):
    return hasattr(type, "__origin__") and type.__origin__


def _check_type(type, value):
    if _check_is_complex_type(type):
        return _check_complex_type(type, value)
    else:
        return _check_simple_type(type, value)


def _check_simple_type(type, value):
    return type is Any or isinstance(value, type)


def _check_complex_type(type, value):
    container_type = type.__origin__
    if container_type is (List if sys.version_info.minor < 7 else list):
        return _check_list_type(type, value)
    elif container_type is (Dict if sys.version_info.minor < 7 else dict):
        return _check_dict_type(type, value)
    elif container_type is (Tuple if sys.version_info.minor < 7 else tuple):
        return _check_tuple_type(type, value)
    elif container_type is Union:
        return _check_union_type(type, value)
    else:
        return isinstance(value, container_type)


def _check_list_type(type, value):
    element_type = type.__args__[0]
    return isinstance(value, list) and (not CHECK_ELEMENTS or all(_check_type(element_type, item) for item in value))


def _check_dict_type(type, value):
    key_type, value_type = type.__args__
    return isinstance(value, dict) and (not CHECK_ELEMENTS or all((_check_type(key_type, k) and _check_type(value_type, v)) for k, v in value.items()))


def _check_tuple_type(type, value):
    types = type.__args__
    return isinstance(value, tuple) and (not CHECK_ELEMENTS or all(_check_type(t, v) for t, v in zip(types, value)))


def _check_union_type(type, value):
    return any(_check_type(t, value) for t in type.__args__)


def _check_function(fn, args, kwargs):
    sig = signature(fn)
    bounded = sig.bind(*args, **kwargs)
    bounded.apply_defaults()
    for name, param in sig.parameters.items():
        _type = param.annotation
        if _type is _empty:
            continue
        if isinstance(_type, str):
            _type = eval(_type)
        value = bounded.arguments[name]
        if not _check_type(_type, value):
            raise TypeError(f"Argument `{name}` of {fn.__name__} needs {_type}")


def type_check(check_elements=False):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            global CHECK_ELEMENTS
            token, CHECK_ELEMENTS = CHECK_ELEMENTS, check_elements
            _check_function(fn, args, kwargs)
            CHECK_ELEMENTS = token
            result = fn(*args, **kwargs)
            return result
        return wrapped
    return decorator


def overload(func):
    registered = [func]

    def register(f):
        registered.append(f)
        return wrapped

    @wraps(func)
    def wrapped(*args, **kwargs):
        for fn in reversed(registered):
            try:
                _check_function(fn, args, kwargs)
            except TypeError:
                continue
            return fn(*args, **kwargs)
        raise TypeError

    wrapped.register = register
    return wrapped
