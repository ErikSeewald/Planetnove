from pygame import Vector2
from util.direction import Direction


class Node:
    """
    Class representing a single node on the planet, abstracted away from it's original role as a 'TileNode'.
    """

    name: str
    coord: Vector2
    paths: dict[Direction, str] # Maps direction to path id

    def __init__(self, name: str, coord: Vector2):
        self.name = name
        self.coord = coord
        self.paths = {direction: "None" for direction in Direction.real_directions_ordered()}

    def set_path(self, direction: Direction, path_id: str):
        if direction is None or direction == Direction.UNKNOWN:
            raise ValueError(f"Node cannot have a path in direction {direction}")

        self.paths[direction] = path_id
