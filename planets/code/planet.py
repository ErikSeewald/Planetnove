from planets.code.node import Node
from planets.code.path import Path


class Planet:
    """
    Class representing a planet.
    While the planet is constructed from tiles, once initialized it ignores the original tile structure completely
    and treats every node and path as belonging to one entity - the planet.
    The joints of the original tiles are no longer considered, instead, a path connected to a joint either becomes
    a path between the two nodes on different tiles that are connected to that joint or 'None' if no such pair exists.
    """

    nodes: dict[str, Node] # Maps node id to Node
    paths: dict[str, Path] # Maps path id to Path

    def __init__(self, nodes: dict[str, Node], paths: dict[str, Path]):
        self.nodes = nodes
        self.paths = paths
