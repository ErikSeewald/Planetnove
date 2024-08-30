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
