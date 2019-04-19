import ratcave as rc

from ..misc.type_check import type_check
from .resources import mesh_reader


@type_check()
def getPlayground(length: int, height: int, width: int):
    # center = mesh_reader.get_mesh("Cube", position=(0, 0, 0), scale=.01)
    playground = []
    for x in range(length):
        for y in range(height):
            # playground.append(mesh_reader.get_mesh("Cube", position=(x, y, 0), scale=.5))
            playground.append(mesh_reader.get_mesh("Cube", position=(x, y, width), scale=.5))
    # for x in range(length):
    #     for z in range(width):
    #         playground.append(mesh_reader.get_mesh("Cube", position=(x, 0, z), scale=.5))
    #         playground.append(mesh_reader.get_mesh("Cube", position=(x, height, z), scale=.5))
    # for x in range(length):
    #     for y in range(height):
    #         playground.append(mesh_reader.get_mesh("Cube", position=(0, y, z), scale=.5))
    #         playground.append(mesh_reader.get_mesh("Cube", position=(length, y, z), scale=.5))
    return playground
