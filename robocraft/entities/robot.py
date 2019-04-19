from .entity import Entity


@Entity.register
class Player(Entity):
    def __init__(self, robot, **kwargs):
        self.robot = robot
        super().__init__(**kwargs)
