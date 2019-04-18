from abc import ABC, abstractmethod
import asyncio
from typing import List

from .entities import Entity
from .events import EventHandler
from .env import current_player, game
from .config import CONFIG


class Robot(ABC, Entity):
    components: List[str] = []

    def __init__(self):
        self.events = EventHandler()

    @abstractmethod
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
