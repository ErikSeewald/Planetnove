class Path:
    """
    Class representing a single path on the planet, abstracted away from it's original role as a 'TilePath'.
    Unlike 'TilePath', a path can only connect nodes together, not joints.
    """

    name: str

    # Node IDs
    node_a: str
    node_b: str

    def __init__(self, name: str, node_a: str, node_b: str):
        self.name = name
        self.node_a = node_a
        self.node_b = node_b
