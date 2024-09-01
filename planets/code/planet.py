from __future__ import annotations
from pygame import Vector2
from planets.code.node import Node
from planets.code.path import Path
from util.direction import Direction


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

    def add_node_with_unknown_paths(self, name: str, coord: Vector2, available_paths: set[Direction]):
        """
        Adds a node with the given name, coordinates and set of available paths to the planet without setting
        the node's 'known_paths' dictionary.
        """

        node = Node(name, coord)
        node.available_paths = available_paths
        self.nodes[name] = node

    def add_path(self, path: Path):
        """
        Adds the given path to the planet. Raises a ValueError if either of the path's nodes are not part of
        the planet.
        """

        if path.node_a not in self.nodes:
            raise ValueError(f"Cannot add path with unknown node {path.node_a}")
        if path.node_b not in self.nodes:
            raise ValueError(f"Cannot add path with unknown node {path.node_b}")

        self.paths[path.name] = path

    def path_exists(self, node_a_with_dir: str, node_b_with_dir: str):
        """
        Returns whether a path described by the two parameters exists on the planet.
        The parameters follow the convention '<node_id>:<Direction abbreviation>'.
        """

        id_a = f"{node_a_with_dir}-{node_b_with_dir}"
        id_b = f"{node_b_with_dir}-{node_a_with_dir}"

        return self.paths.get(id_a) or self.paths.get(id_b)

    def to_dict(self) -> dict:
        return {
            "nodes": {name: n.to_dict() for name, n in self.nodes.items()},
            "paths": {name: p.to_dict() for name, p in self.paths.items()}
        }

    @staticmethod
    def from_dict(planet_dict: dict) -> Planet:
        return Planet(
            nodes={name: Node.from_dict(n) for name, n in planet_dict['nodes'].items()},
            paths={name: Path.from_dict(p) for name, p in planet_dict['paths'].items()}
        )

    def __str__(self) -> str:
        return f"Nodes: {self.nodes}\nPaths: {self.paths}"

