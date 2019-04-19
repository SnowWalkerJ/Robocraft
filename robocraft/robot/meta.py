import asyncio
from functools import wraps
import inspect

from .. import env


class APIMeta(type):
    def __new__(cls, name, bases, attrs):
        new_attrs = {}
        for attr_name, attr in attrs.items():
            if hasattr(attr, 'is_api'):
                if inspect.iscoroutinefunction(attr):
                    fn_name = attr_name.strip("_")
                    attr = wraps(attr)(cls.__make_async_func(fn_name))
                elif inspect.isfunction(attr):
                    fn_name = attr_name.strip("_")
                    attr = wraps(attr)(cls.__make_func(fn_name))
            new_attrs[attr_name] = attr
        return type.__new__(cls, name, bases, new_attrs)

    @classmethod
    def __make_async_func(cls, name):
        async def fn(player, *args, **kwargs):
            game = env.game.get()
            await cls.__delay(game, player, name)
            f = getattr(game, name)
            if inspect.iscoroutinefunction(f):
                return await f(player, *args, **kwargs)
            else:
                return f(player, *args, **kwargs)
        return fn

    @staticmethod
    def __make_func(name):
        def fn(palyer, *args, **kwargs):
            game = env.game.get()
            return getattr(game, name)(player, *args, **kwargs)
        fn.name = name
        return fn

    @staticmethod
    async def __delay(world, player, name):
        delay = world.getTimeCosts(player).get(name, 0)
        if delay:
            print("delay", delay, "ticks")
            await asyncio.sleep(delay * world.TICK)


def api(fn):
    fn.is_api = True
    return fn
