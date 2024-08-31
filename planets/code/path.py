from __future__ import annotations
from util.direction import Direction


class Path:
    """
    Class representing a single path on the planet, abstracted away from it's original role as a 'TilePath'.
    Unlike 'TilePath', a path can only connect nodes together, not joints.
    """

    name: str

    # Node IDs
    node_a: str
    node_b: str

    direction_a: Direction
    direction_b: Direction

    def __init__(self, name: str, node_a_with_dir: str, node_b_with_dir: str):
        self.name = name

        split_a = node_a_with_dir.split(":")
        split_b = node_b_with_dir.split(":")

        self.node_a = split_a[0]
        self.node_b = split_b[0]

        self.direction_a = Direction.from_str(split_a[1])
        self.direction_b = Direction.from_str(split_b[1])

    def __str__(self):
        return self.name

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "node_a": self.node_a,
            "node_b": self.node_b,
            "direction_a": self.direction_a.abbreviation(),
            "direction_b": self.direction_b.abbreviation()
        }

    @staticmethod
    def from_dict(path_dict: dict) -> Path:
        return Path(name=path_dict['name'],
                    node_a_with_dir=f"{path_dict['node_a']}:{path_dict['direction_a']}",
                    node_b_with_dir=f"{path_dict['node_b']}:{path_dict['direction_b']}")
