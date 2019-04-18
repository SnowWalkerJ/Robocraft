from .meta import APIMeta
from .. import env


class RobotAPI(metaclass=APIMeta):
    async def getStatus():
        pass

    async def moveForward():
        pass

    async def moveBackward():
        pass

    async def moveUpward():
        pass

    async def moveDownward():
        pass

    async def rotateLeft():
        pass

    async def rotateRight():
        pass

    async def attack():
        pass

    async def defend():
        pass

    async def halt(ticks):
        """Do nothing, and wait for n ticks to pass"""

    async def senseForward():
        pass

    async def senseSurroundings():
        pass

    def getProperties():
        pass

    def getEnhancements():
        pass

    def getTimeCosts():
        pass
