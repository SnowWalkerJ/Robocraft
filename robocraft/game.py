import asyncio
from collections import defaultdict
import contextvars
from numbers import Number
from typing import List, Tuple, Set

from .config import CONFIG
from .entities import Entity
from . import env
from .robot import Robot
from .utils.vector import Vector
from .utils.property import Property
from . import exceptions


class Game:
    def __init__(self):
        self.__ready: bool = False
        self.__TICK: float = 1 / CONFIG['init']['game']['ticksPerSec']
        self.__entities: Dict[Entity, Dict] = {}
        self.__players: Set[Robot] = set()
        self.__height: int = CONFIG['init']['room']['height']
        self.__width: int = CONFIG['init']['room']['width']
        self.__length: int = CONFIG['init']['room']['length']
        self.__spwan_status = [
            (Vector(-(self.__width // 2), 0, 0), Vector(1, 0, 0)),
            (Vector(self.__width // 2, 0, 0), Vector(-1, 0, 0)),
            (Vector(0, 0, -(self.__length // 2)), Vector(0, 0, 1)),
            (Vector(0, 0, self.__length // 2), Vector(0, 0, -1)),
        ]

    def run(self):
        print(self.__spwan_status)
        env.game.set(self)
        for player in self.__players:
            context = contextvars.copy_context()
            context.run(player.main)
        asyncio.ensure_future(self.loop())
        self.__ready = True
        asyncio.get_event_loop().run_forever()

    async def loop(self):
        while 1:
            for entity in self.__entities.keys():
                print(entity, self._get_status(entity, 'location'))
            await asyncio.sleep(1)

    def is_ready(self) -> bool:
        return self.__ready

    @property
    def TICK(self) -> float:
        return self.__TICK

    def register(self, player: Robot):
        self._check_capacity(player.components)
        enhancement = self._components_enhancement(player.components)
        timecosts = CONFIG['ticks']
        real_timecosts = {key: value / (enhancement['speed'].default + 1) for key, value in timecosts.items()}
        location, direction = self._get_next_spawn_status()
        properties = {key: Property(value) * (enhancement[key] + 1) for key, value in CONFIG['init']['player']['properties'].items()}
        self.__entities[player] = {
            "init": {
                "enhancements": enhancement,
                "timeCosts": real_timecosts,
                "properties": properties,
            },
            "status": {
                "location": location,
                "direction": direction,
                "health": properties['health'],
            }
        }
        self.__players.add(player)

    def _check_capacity(self, components: List[str]):
        capacities = CONFIG['init']['player']['capacity'].copy()
        for component in components:
            if component not in CONFIG['components']:
                raise ValueError(f"Invalid component {component}")
            for key, value in CONFIG['components'][component]['costs'].items():
                capacities[key] -= value
                if capacities[key] < 0:
                    raise exceptions.CapacityExceed

    def _components_enhancement(self, components: List[str]) -> dict:
        enhancement = defaultdict(lambda: Property(0.0))
        for component in components:
            properties = CONFIG['components'][component]['properties']
            for key, value in properties.items():
                enhancement[key] = enhancement[key] + Property(value)
        return enhancement

    def _get_next_spawn_status(self) -> Tuple[Vector, Vector]:
        return self.__spwan_status.pop()

    def _has_entity(self, loc: Vector):
        if not (-self.__length // 2 <= loc.x <= self.__length and
                -self.__width // 2 <= loc.z <= self.__width and
                -self.__height // 2 <= loc.y <= self.__height):
            return Entity.Wall
        for player in self.__entities.keys():
            if self._get_status(player, "location") == loc:
                return player
        return None

    def _set_status(self, player, attr, value):
        print("BeforeSetStatus", self.__entities[player]['status'][attr])
        self.__entities[player]['status'][attr] = value
        print("AfterSetStatus", self.__entities[player]['status'][attr])

    def _get_status(self, player, attr=None):
        if attr:
            return self.__entities[player]['status'][attr]
        else:
            return self.__entities[player]['status'].copy()

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

    def _calc_harm(self, source: Robot, target: Robot) -> float:
        attacks = self.getProperties(source)['attack']
        defenses = self.getProperties(source)['defense']
        if self._get_relative_status(source, target)['direction'] == Vector(1, 0, 0):
            attack, defense = attacks['back'], defenses['back']
        else:
            attack, defense = attacks['normal'], defenses['normal']
        return attack / defense

    def tolist(self):
        background = [["."] * self.__length for _ in range(self._width)]
        for entity in self.__entities.keys():
            x, y, z = self._get_status(entity, "location")
            background[x][z] = "x"
        return background

    # ======================= API ======================= #

    def getStatus(self, player: Robot):
        return self._get_relative_status(player, player)

    def moveForward(self, player: Robot):
        return self.__move(player, self._get_status(player, 'direction'))

    def moveBackward(self, player: Robot):
        return self.__move(player, -self._get_status(player, 'direction'))

    def moveUpward(self, player: Robot):
        return self.__move(player, Vector(0, 1, 0))

    def moveDownward(self, player: Robot):
        return self.__move(player, Vector(0, -1, 0))

    def rotateLeft(self, player: Robot):
        return self.__rotate(player, Vector(1, 0, 0))

    def rotateRight(self, player: Robot):
        return self.__rotate(player, Vector(-1, 0, 0))

    def attack(self, player: Robot):
        facing_location = self._get_status(player, 'location') + self._get_status(player, 'direction')
        entity = self._has_entity(facing_location)
        if entity and isinstance(entity, Robot):
            harm = self._calc_harm(player, entity)
            health = self._get_status(entity, "health")
            self._set_status(entity, "health", health - harm)
            entity.events.fire("attacked", source=self._get_relative_status(entity, player), harm=harm)
            if health <= 0:
                entity.events.fire("dead")
                player.events.fire("kills")

    def defend(self, player: Robot):
        pass

    async def halt(self, player: Robot, ticks: int):
        await asyncio.sleep(ticks * self.TICK)

    def senseForward(self, player: Robot):
        entities = []
        my_location = self._get_status(player, "location")
        for entity in self.__entities.keys():
            if entity is player:
                continue
            target_location = self._get_status(entity, "location")
            relative_location = target_location - my_location
            if relative_location @ my_direction <= CONFIG['init']['game']['fogDistance']:
                status = self._get_relative_status(player, entity)
                entities.append(status)
        return entities

    def senseSurroundings(self, player: Robot):
        distance: float = CONFIG['init']['game']['surroundingDistance']
        entities = []
        my_location = self._get_status(player, "location")
        for entity in self.__entities.keys():
            if entity is player:
                continue
            target_location = self._get_status(entity, "location")
            relative_location = target_location - my_location
            if abs(relative_location) <= CONFIG['init']['game']['surroundingDistance']:
                status = self._get_relative_status(player, entity)
                entities.append(status)
        return entities

    def __move(self, player: Robot, direction: Vector):
        print("moving", direction)
        location = self._get_status(player, 'location')
        new_location = location + direction
        if not self._has_entity(new_location):
            print(location, new_location)
            self._set_status(player, 'location', new_location)
        else:
            print("blocked")

    def __rotate(self, player: Robot, offset: Vector):
        direction = self._get_status(player, 'direction')
        self._set_status(player, "direction", direction * offset)

    def getProperties(self, player: Robot):
        return self.__entities[player]['init']['properties'].copy()

    def getEnhancements(self, player: Robot):
        return self.__entities[player]['init']['enhancements'].copy()

    def getTimeCosts(self, player: Robot):
        return self.__entities[player]['init']['timeCosts'].copy()

    def getSize(self, player: Robot):
        return (self.__length, self.__height, __self.__width)
