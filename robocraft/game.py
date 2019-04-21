import asyncio
from collections import defaultdict
import copy
import contextvars
from functools import wraps
import inspect
from numbers import Number
from typing import List, Tuple, Set
from uuid import UUID

from .config import CONFIG
from .entities import Entity, EntityFactory
from .events import EventHandler
from . import env
from .robot import Robot
from .utils.vector import Vector
from .utils.property import *
from . import exceptions


def delay(fn):
    @wraps(fn)
    async def wrapped(self, player, *args, **kwags):
        fn_name = fn.__qualname__.split(".")[-1]
        delay = getattr(self.getTimeCosts(player), fn_name, 0)
        if delay:
            delay = max(int(delay), 1)
            await asyncio.sleep(delay * env.TICK.get())
        if inspect.iscoroutinefunction(fn):
            return await fn(self, player, *args, **kwags)
        else:
            return fn(self, player, *args, **kwags)
    return wrapped


class Game:
    def __init__(self):
        self.events = EventHandler()
        env.TICK.set(1 / CONFIG['init']['game']['ticksPerSec'])
        self.__ready: bool = False
        self.__alive_count = 0
        self.__entities = EntityFactory()
        self.__entity_status: Dict[Entity, Dict] = {}
        self.__players: Dict[UUID, Entity.Player] = {}
        self.__height: int = CONFIG['init']['room']['height']
        self.__width: int = CONFIG['init']['room']['width']
        self.__length: int = CONFIG['init']['room']['length']
        self.__spwan_status = [
            (Vector(-(self.__length // 2), 0, 0), Vector(1, 0, 0)),
            (Vector(self.__length // 2, 0, 0), Vector(-1, 0, 0)),
            (Vector(0, 0, -(self.__width // 2)), Vector(0, 0, 1)),
            (Vector(0, 0, self.__width // 2), Vector(0, 0, -1)),
        ]

    def run(self):
        env.game.set(self)
        self.events.register("kills", self.evnt_kills)
        for player in self.__players.values():
            context = contextvars.copy_context()
            context.run(player.main)
        self.__ready = True
        asyncio.get_event_loop().run_until_complete(self.loop())

    async def loop(self):
        while self.__alive_count > 1:
            # for entity in self.__entity_status.keys():
            #     print(entity, self._get_status(entity, 'location'))
            await asyncio.sleep(env.TICK.get())
            await self.events.poll()

    def is_ready(self) -> bool:
        return self.__ready

    def register(self, player: Robot):
        entity = self.entities.get_or_create(player.uuid, Entity.Player, player)
        self._check_capacity(player.components)
        enhancement = self._components_enhancement(player.components)
        origin_property = RobotProperty(**CONFIG['init']['player']['properties'])
        enhanced_property = origin_property * (enhancement + 1)
        location, direction = self._get_next_spawn_status()
        self.__entity_status[entity] = {
            "type": Entity.Player,
            "uuid": player.uuid,
            "enhancements": enhancement,
            "timeCosts": SpeedProperty(**CONFIG['ticks']) / (enhanced_property.speed + 1),
            "properties": enhanced_property,
            "location": location,
            "direction": direction,
            "alive": True,
        }
        self.__players[player.uuid] = player
        self.__alive_count += 1

    def __create_wall(self, x: int, y: int, z: int):
        wall = self.entities.create(Entity.Wall)
        self.__entity_status[wall] = {
            "init": {
                "type": Entity.Wall,
                "uuid": wall.uuid,
            },
            "status": {
                "location": Vector(x, y, z),
            }
        }

    def __construct_walls(self):
        for x in range(-self.length // 2, self.length // 2 + 1):
            for y in range(-self.height // 2, self.height // 2 + 1):
                self.__create_wall(x, y, -self.width // 2)
                self.__create_wall(x, y, self.width // 2)

        for x in range(-self.length // 2, self.length // 2 + 1):
            for z in range(-self.width // 2, self.width // 2 + 1):
                self.__create_wall(x, -self.height // 2, z)
                self.__create_wall(x, self.height // 2, z)

        for z in range(-self.width // 2, self.width // 2 + 1):
            for y in range(-self.height // 2, self.height // 2 + 1):
                self.__create_wall(-self.length // 2, y, z)
                self.__create_wall(self.length // 2, y, z)

    def _check_capacity(self, components: List[str]):
        capacities = CapacityProperty(**CONFIG['init']['player']['properties']['capacity'])
        for component in components:
            if component not in CONFIG['components']:
                raise ValueError(f"Invalid component {component}")
            cost = CapacityProperty(**CONFIG['components'][component]['costs'])
            capacities = capacities - cost
        if capacities.weight < 0 or capacities.space < 0:
            raise ValueError("Capacity exceeded")

    def _components_enhancement(self, components: List[str]) -> dict:
        enhancement = ComponentProperty()
        for component in components:
            properties = ComponentProperty(**CONFIG['components'][component]['properties'])
            enhancement = enhancement + properties
        return enhancement

    def _get_next_spawn_status(self) -> Tuple[Vector, Vector]:
        return self.__spwan_status.pop()

    def _has_entity(self, loc: Vector):
        if not (-self.__length // 2 <= loc.x <= self.__length and
                -self.__width // 2 <= loc.z <= self.__width and
                -self.__height // 2 <= loc.y <= self.__height):
            return Entity.Wall
        for player in self.__entity_status.keys():
            if self._get_status(player, "location") == loc:
                return player
        return None

    def _set_status(self, player: Entity, attr, value):
        if attr in ("location", "direction"):
            self.__entity_status[player][attr] = value
        else:
            setattr(self.__entity_status[player]["properties"], attr, value)

    def _get_status(self, player: Entity, attr=None):
        if attr:
            if attr in ("location", "direction"):
                return self.__entity_status[player][attr]
            else:
                return getattr(self.__entity_status[player]['properties'], attr)
        else:
            return copy.deepcopy(self.__entity_status[player])

    def _get_relative_status(self, origin: Entity, other: Entity) -> dict:
        origin_location = self._get_status(origin, "location")
        origin_direction = self._get_status(origin, "direction")
        other_location = self._get_status(other, "location")
        other_direction = self._get_status(other, "direction")
        relative_location = (other_location - origin_location) * origin_direction
        relative_direction = other_direction * origin_direction
        status = self._get_status(other)
        status['location'] = relative_location
        status['direction'] = relative_direction
        return status

    def _calc_harm(self, source: Entity.Player, target: Entity.Player) -> float:
        attacks = self.getProperties(source).attack
        defenses = self.getProperties(target).defense
        if self._get_relative_status(source, target)['direction'] == Vector(1, 0, 0):
            attack, defense = attacks.back, defenses.back
        else:
            attack, defense = attacks.normal, defenses.normal
        return attack / defense

    def tolist(self):
        background = [["."] * self.__length for _ in range(self._width)]
        for entity in self.__entity_status.keys():
            x, y, z = self._get_status(entity, "location")
            background[x][z] = "x"
        return background

    @property
    def entities(self):
        return self.__entities

    @property
    def length(self):
        return self.__length

    @property
    def width(self):
        return self.__width

    @property
    def height(self):
        return self.__height

    # ====================== Events ===================== #

    async def evnt_kills(self, source: Entity.Player, target: Entity.Player):
        self.__entity_status[target]['alive'] = False
        self.__alive_count -= 1

    # ======================= API ======================= #

    @delay
    def getStatus(self, player: Entity.Player):
        return self._get_relative_status(player, player)

    @delay
    def moveForward(self, player: Entity.Player):
        return self.__move(player, self._get_status(player, 'direction'))

    @delay
    def moveBackward(self, player: Entity.Player):
        return self.__move(player, -self._get_status(player, 'direction'))

    @delay
    def moveUpward(self, player: Entity.Player):
        return self.__move(player, Vector(0, 1, 0))

    @delay
    def moveDownward(self, player: Entity.Player):
        return self.__move(player, Vector(0, -1, 0))

    @delay
    def rotateLeft(self, player: Entity.Player):
        return self.__rotate(player, Vector(1, 0, 0))

    @delay
    def rotateRight(self, player: Entity.Player):
        return self.__rotate(player, Vector(-1, 0, 0))

    @delay
    def attack(self, player: Entity.Player):
        facing_location = self._get_status(player, 'location') + self._get_status(player, 'direction')
        entity = self._has_entity(facing_location)
        if entity and isinstance(entity, Entity.Player):
            harm = self._calc_harm(player, entity)
            health = self._get_status(entity, "hp") - harm
            self._set_status(entity, "hp", health)
            entity.robot.events.fire("attacked", source=self._get_relative_status(entity, player), harm=harm)
            if health <= 0:
                self.events.fire("kills", player, entity)
                entity.robot.events.fire("dead")
                player.robot.events.fire("kills")

    @delay
    def defend(self, player: Entity.Player):
        pass

    @delay
    async def halt(self, player: Entity.Player, ticks: int):
        await asyncio.sleep(ticks * env.TICK.get())

    @delay
    def senseForward(self, player: Entity.Player):
        entities = []
        my_location = self._get_status(player, "location")
        for entity in self.__entity_status.keys():
            if entity is player:
                continue
            target_location = self._get_status(entity, "location")
            relative_location = target_location - my_location
            if relative_location @ my_direction <= CONFIG['init']['game']['fogDistance']:
                status = self._get_relative_status(player, entity)
                entities.append(status)
        return entities

    @delay
    def senseSurroundings(self, player: Entity.Player):
        distance: float = CONFIG['init']['game']['surroundingDistance']
        entities = []
        my_location = self._get_status(player, "location")
        for entity in self.__entity_status.keys():
            if entity is player:
                continue
            target_location = self._get_status(entity, "location")
            relative_location = target_location - my_location
            if abs(relative_location) <= CONFIG['init']['game']['surroundingDistance']:
                status = self._get_relative_status(player, entity)
                entities.append(status)
        return entities

    def __move(self, player: Entity.Player, direction: Vector):
        location: Vector = self._get_status(player, 'location')
        new_location: Vector = location + direction
        if not self._has_entity(new_location):
            self._set_status(player, 'location', new_location)
        else:
            print("blocked")

    def __rotate(self, player: Entity.Player, offset: Vector):
        direction: Vector = self._get_status(player, 'direction')
        self._set_status(player, "direction", direction * offset)

    def getProperties(self, player: Entity.Player):
        return copy.deepcopy(self.__entity_status[player]['properties'])

    def getEnhancements(self, player: Entity.Player):
        return copy.deepcopy(self.__entity_status[player]['enhancements'])

    def getTimeCosts(self, player: Entity.Player):
        return copy.deepcopy(self.__entity_status[player]['timeCosts'])

    def getSize(self, player: Entity.Player):
        return (self.__length, self.__height, __self.__width)
