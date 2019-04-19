import asyncio
from functools import wraps
import inspect

from .. import env


class APIMeta(type):
    def __new__(cls, name, bases, attrs):
        new_attrs = {}
        for attr_name, attr in attrs.items():
            if hasattr(attr, 'is_api'):
                if attr_name.startswith("get"):
                    fn_name = attr_name.strip("_")
                    attr = wraps(attr)(cls.__make_func(fn_name))
                else:
                    fn_name = attr_name.strip("_")
                    attr = wraps(attr)(cls.__make_async_func(fn_name))
            new_attrs[attr_name] = attr
        return type.__new__(cls, name, bases, new_attrs)

    @classmethod
    def __make_async_func(cls, name):
        async def fn(player, *args, **kwargs):
            game = env.game.get()
            f = getattr(game, name)
            entity = game.entities.get_or_create(player.uuid)
            if inspect.iscoroutinefunction(f):
                return await f(entity, *args, **kwargs)
            else:
                return f(entity, *args, **kwargs)
        return fn

    @staticmethod
    def __make_func(name):
        def fn(player, *args, **kwargs):
            game = env.game.get()
            entity = game.entities.get_or_create(player.uuid)
            return getattr(game, name)(entity, *args, **kwargs)
        fn.name = name
        return fn


def api(fn):
    fn.is_api = True
    return fn
