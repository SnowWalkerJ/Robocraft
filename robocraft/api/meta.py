import asyncio
import inspect

from .. import env


class APIMeta(type):
    def __new__(cls, name, bases, attrs):
        new_attrs = {}
        for attr_name, attr in attrs.items():
            if inspect.iscoroutinefunction(attr):
                fn_name = attr_name.strip("_")
                attr = cls.__make_async_func(fn_name)
            elif inspect.isfunction(attr):
                fn_name = attr_name.strip("_")
                attr = cls.__make_func(fn_name)
            new_attrs[attr_name] = attr
        return type.__new__(cls, name, bases, new_attrs)

    @classmethod
    def __make_async_func(cls, name):
        async def fn(*args, **kwargs):
            game = env.game.get()
            player = env.current_player.get()
            await cls.__delay(game, player, name)
            f = getattr(game, name)
            if inspect.iscoroutinefunction(f):
                return await f(player, *args, **kwargs)
            else:
                return f(player, *args, **kwargs)
        return staticmethod(fn)

    @staticmethod
    def __make_func(name):
        def fn(*args, **kwargs):
            game = env.game.get()
            player = env.current_player.get()
            return getattr(game, name)(player, *args, **kwargs)
        fn.name = name
        return staticmethod(fn)

    @staticmethod
    async def __delay(world, player, name):
        delay = world.getTimeCosts(player).get(name, 0)
        if delay:
            print("delay", delay, "ticks")
            await asyncio.sleep(delay * world.TICK)
