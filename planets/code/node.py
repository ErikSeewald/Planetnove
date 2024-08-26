from pygame import Vector2
from util.direction import Direction


class Node:
    """
    Class representing a single node on the planet, abstracted away from it's original role as a 'TileNode'.
    """

    name: str
    coord: Vector2
    known_paths: dict[Direction, str] # Maps direction to path id

    # All paths that do not lead to 'None'. A path can be available but not yet in known_paths if the node it leads
    # to is still unknown
    available_paths: set[Direction]

    def __init__(self, name: str, coord: Vector2):
        self.name = name
        self.coord = coord

        self.available_paths = set()
        self.known_paths = {direction: "None" for direction in Direction.real_directions_ordered()}

    def set_path(self, direction: Direction, path_id: str):
        if direction is None or direction == Direction.UNKNOWN:
            raise ValueError(f"Node cannot have a path in direction {direction}")

        self.known_paths[direction] = path_id
        self.available_paths.add(direction)

    def make_path_unknown(self, direction: Direction):
        self.known_paths.pop(direction)

    def make_path_unavailable(self, direction: Direction):
        self.available_paths.remove(direction)
        self.known_paths.pop(direction)
