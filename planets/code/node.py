from __future__ import annotations
from pygame import Vector2
from util.direction import Direction


class Node:
    """
    Class representing a single node on the planet, abstracted away from it's original role as a 'TileNode'.
    """

    name: str
    coord: Vector2
    direction_to_path_id: dict[Direction, str]

    # All paths that do not lead to 'None'. A path can be available but not yet mapped to
    # anything in direction_to_path_id if the node it leads to is still unknown
    available_paths: set[Direction]

    def __init__(self, name: str, coord: Vector2):
        self.name = name
        self.coord = coord

        self.available_paths = set()
        self.direction_to_path_id = {direction: "None" for direction in Direction.real_directions_ordered()}

    def set_path(self, direction: Direction, path_id: str):
        """
        Sets the path at the given direction to the given path_id in direction_to_path_id.
        """

        if direction is None or direction == Direction.UNKNOWN:
            raise ValueError(f"Node cannot have a path in direction {direction}")

        self.direction_to_path_id[direction] = path_id
        self.available_paths.add(direction)

    def make_path_unknown(self, direction: Direction):
        """
        Removes the path at the given direction from direction_to_path_id.
        The direction remains in the set of available paths.
        """

        self.direction_to_path_id.pop(direction)

    def make_path_unavailable(self, direction: Direction):
        """
        Removes the direction from the node's set of available paths and from direction_to_path_id.
        """

        self.available_paths.remove(direction)
        self.direction_to_path_id.pop(direction)

    def has_unexplored_paths(self) -> bool:
        """
        Returns whether there are available paths at this node that have not yet been added to direction_to_path_id.
        """

        for direction in self.available_paths:
            if self.direction_to_path_id.get(direction) == "None":
                return True
        return False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "coord": {"x": self.coord.x, "y": self.coord.y},
            "direction_to_path_id": {d.name: p for d, p in self.direction_to_path_id.items()},
            "available_paths": [d.name for d in self.available_paths]
        }

    @staticmethod
    def from_dict(node_dict: dict) -> Node:
        node = Node(name=node_dict['name'], coord=Vector2(node_dict['coord']['x'], node_dict['coord']['y']))
        node.direction_to_path_id = {Direction.from_str(d): p for d, p in node_dict['direction_to_path_id'].items()}
        node.available_paths = {Direction.from_str(d) for d in node_dict['available_paths']}
        return node
