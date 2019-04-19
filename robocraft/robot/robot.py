import asyncio
from typing import List
from uuid import uuid4

from ..entities import Entity
from ..events import EventHandler
from ..env import current_player, game
from ..config import CONFIG
from .meta import APIMeta, api


class Robot(metaclass=APIMeta):
    components: List[str] = []

    def __init__(self):
        self.events = EventHandler()
        self.__uuid = uuid4()

    @property
    def uuid(self):
        return self.__uuid

    async def run(self):
        pass

    def main(self):
        current_player.set(self)
        self.game = game.get()

        async def _():
            while not self.game.is_ready():
                await asyncio.sleep(self.game.TICK * 0.5)
            await self.run()

        asyncio.ensure_future(_())

    # ------------------------- API ------------------------- #

    @api
    async def getStatus(self):
        pass

    @api
    async def moveForward(self):
        pass

    @api
    async def moveBackward(self):
        pass

    @api
    async def moveUpward(self):
        pass

    @api
    async def moveDownward(self):
        pass

    @api
    async def rotateLeft(self):
        pass

    @api
    async def rotateRight(self):
        pass

    @api
    async def attack(self):
        pass

    @api
    async def defend(self):
        pass

    @api
    async def halt(self, ticks):
        """Do nothing, and wait for n ticks to pass"""

    @api
    async def senseForward(self):
        pass

    @api
    async def senseSurroundings(self):
        pass

    @api
    def getProperties(self):
        pass

    @api
    def getEnhancements(self):
        pass

    @api
    def getTimeCosts(self):
        pass

    @api
    def getSize(self):
        pass
