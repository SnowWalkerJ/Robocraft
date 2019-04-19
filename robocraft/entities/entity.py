from typing import Type, Optional
from uuid import uuid4, UUID


class Entity:
    visible: bool = True

    def __init__(self, **kwargs):
        self.visible = self.__class__.visible
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def register(cls, subclass: type):
        setattr(cls, subclass.__qualname__, subclass)

    def __eq__(self, other):
        return self.uuid == other.uuid

    def __hash__(self):
        return hash(self.uuid)


class EntityFactory:
    def __init__(self):
        self.entities = {}

    def get_or_create(self, uuid: UUID, entity_type: Optional[Type[Entity]]=None, *args, **kwargs) -> Entity:
        if uuid in self.entities:
            return self.entities[uuid]
        elif entity_type is not None:
            obj = entity_type(*args, **kwargs)
            obj.uuid = uuid
            self.entities[uuid] = obj
            return obj
        else:
            raise KeyError(f"Can't find entity with uuid {uuid}")

    def create(self, entity_type: Optional[Type[Entity]]=None, *args, **kwargs) -> Entity:
        obj = entity_type(*args, **kwargs)
        obj.uuid = uuid4()
        self.entities[obj.uuid] = obj
        return obj

    def keys(self):
        return self.entities.keys()
