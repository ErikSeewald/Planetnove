from __future__ import annotations
from util.direction import Direction
from planets.code.node import Node


class Path:
    """
    Class representing a single path on the planet, abstracted away from it's original role as a 'TilePath'.
    Unlike 'TilePath', a path only connects nodes together, not joints.
    """

    id: str
    length: float

    # Node IDs
    node_a: str
    node_b: str

    direction_a: Direction
    direction_b: Direction

    def __init__(self, id_dir_key_a: str, id_dir_key_b: str, length: float = 1):
        self.id = Path.id_from_node_keys(id_dir_key_a, id_dir_key_b)
        self.length = length

        split_a = id_dir_key_a.split(":")
        split_b = id_dir_key_b.split(":")

        self.node_a = split_a[0]
        self.node_b = split_b[0]

        self.direction_a = Direction.from_str(split_a[1])
        self.direction_b = Direction.from_str(split_b[1])

    def contains_id_dir_key(self, id_dir_key: str) -> bool:
        """
        Returns whether the path_id contains the given id_dir_key as a node.
        Use this method instead of manual string checking in case the id implementation
        ends up changing.
        """

        return id_dir_key in self.id

    @staticmethod
    def id_from_node_keys(id_dir_key_a: str, id_dir_key_b: str) -> str:
        """
        Returns the <id_dir_key_a>-<id_dir_key_b> path id for the given parameters.
        """

        return f"{id_dir_key_a}-{id_dir_key_b}"

    def __str__(self):
        return self.id

    def to_dict(self) -> dict:
        return {
            # self.id can be excluded as it is fully dependent on the nodes and directions
            "node_a": self.node_a,
            "node_b": self.node_b,
            "direction_a": self.direction_a.abbreviation(),
            "direction_b": self.direction_b.abbreviation(),
            "length": self.length
        }

    @staticmethod
    def from_dict(path_dict: dict) -> Path:
        return Path(
            id_dir_key_a=Node.id_direction_key(
                path_dict['node_a'], Direction.from_str(path_dict['direction_a'])
            ),
            id_dir_key_b=Node.id_direction_key(
                path_dict['node_b'], Direction.from_str(path_dict['direction_b'])
            ),
            length=float(path_dict['length'])
        )
