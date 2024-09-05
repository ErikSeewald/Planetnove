from __future__ import annotations
import heapq as heap

from mypyc.transform.exceptions import adjust_error_kinds
from pygame import Vector2
from planets.code.node import Node
from planets.code.path import Path
from planets.code.route import Route
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
        the node's direction_to_path_id dictionary.
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

    def shortest_routes_from(self, from_id: str) -> dict[str, Route]:
        """
        Returns the shortest routes (based on the path's 'length' attribute) from the node described by the given id
        to all other nodes on the planet using dijkstra. If there is no route to a node, then there will be no
        entry in the dictionary.

        :returns: Dict mapping the id of the target node to the Route connecting it to the node described by 'from_id'
        """

        # maps child id to tuple of (parent_id, connecting_path_id)
        # e.g. If the shortest route from A to D contains the path B->C then parents[C] = (B, B->C)
        parents: dict[str, tuple[str, str]] = dict()

        visited: set[str] = set()  # IDs of visited nodes
        queue: list[tuple[float, str]] = list()  # list of (weight, node_id) of queued nodes

        weights: dict[str, float] = dict()  # maps node_id to its current_weight
        weights.update({from_id: 0})

        # heap keeps node with lowest weight at the top of the queue
        heap.heappush(queue, (0, from_id))

        while queue:
            old_weight, node_id = heap.heappop(queue)
            visited.add(node_id)

            cur_node = self.nodes.get(node_id)
            for direction, path_id in cur_node.direction_to_path_id.items():
                if path_id == "None":
                    continue  # Ignore unknown paths

                cur_path = self.paths.get(path_id)
                if cur_path.node_a == cur_path.node_b:
                    continue  # Ignore looping paths

                adjacent_id = cur_path.node_a if node_id == cur_path.node_b else cur_path.node_b

                if adjacent_id in visited:
                    continue
                if weights.get(adjacent_id) is None:
                    weights[adjacent_id] = float("inf")

                new_weight = weights.get(node_id) + cur_path.length
                if new_weight < weights.get(adjacent_id):
                    parents[adjacent_id] = (node_id, cur_node.direction_to_path_id.get(direction))
                    weights[adjacent_id] = new_weight
                    heap.heappush(queue, (new_weight, adjacent_id))

        # Build routes
        routes: dict[str, Route] = dict()
        for node_id, node in self.nodes.items():
            if node_id == from_id:
                routes[node_id] = Route(from_id, node_id, 0, list())

            path_id_list: list[str] = list()
            cur_node = node_id
            cur_parents = parents.get(cur_node)
            if cur_parents is None:
                continue  # No route exists

            while cur_node != from_id:  # walk backwards to the starting node
                path_id_list.append(cur_parents[1])
                cur_node = cur_parents[0]
                cur_parents = parents.get(cur_node)

            routes[node_id] = Route(from_id, node_id, weights[node_id], path_id_list)
        return routes

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

