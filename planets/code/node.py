from __future__ import annotations
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

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "coord": {"x": self.coord.x, "y": self.coord.y},
            "known_paths": {d.name: p for d, p in self.known_paths.items()},
            "available_paths": [d.name for d in self.available_paths]
        }

    @staticmethod
    def from_dict(node_dict: dict) -> Node:
        node = Node(name=node_dict['name'], coord=Vector2(node_dict['coord']['x'], node_dict['coord']['y']))
        node.known_paths = {Direction.from_str(d): p for d, p in node_dict['known_paths'].items()}
        node.available_paths = {Direction.from_str(d) for d in node_dict['available_paths']}
        return node
