from __future__ import annotations
from dataclasses import dataclass, field
from pygame import Vector2
from util.direction import Direction


@dataclass
class TilePath:
    """
    Dataclass representing a path on the tile. Each path needs a unique combination of from/to indicators.
    These can be different or the same but a local tile path is never allowed to lead to 'None'.
    They can be nodes (format: <node_name>:<Direction> where Direction is one of ['N', 'E', 'S', 'W']
    or joints (format: <joint_id> (e.g. 'jointN2' for the second joint at the northern side))
    """

    name: str
    from_: str
    to_: str

    def __init__(self, from_: str, to_: str):
        self.from_ = from_
        self.to_ = to_
        self.name = f"{self.from_}-{self.to_}"


@dataclass
class TileNode:
    """
    Dataclass representing a node on the tile. Each node needs a unique name.
    It has node coordinates in the range ([0,4], [0,4])
    and absolute tile coordinates (in mm and in the range ([0, 1000], [0, 1000])).
    The way node coordinates map to tile coordinates is described further in the documentation.
    """

    name: str
    node_coord: Vector2
    tile_coord: Vector2

    def __init__(self, name: str, node_coord: list[int]):
        self.name = name
        self.node_coord = validate_node_coord(node_coord, name)
        self.tile_coord = convert_tile_coord(node_coord, name)


@dataclass
class TileJoint:
    """
    Dataclass representing a joint on the tile. Each joint needs a unique name
    (e.g. 'jointN2' for the second joint at the northern side)).
    It has node coordinates in the range ([0,4], [0,4])
    and absolute tile coordinates (in mm and in the range ([0, 1000], [0, 1000])).
    The way node coordinates map to tile coordinates is described further in the documentation.
    """

    name: str
    node_coord: Vector2
    tile_coord: Vector2

    def __init__(self, name: str, node_coord: list[int]):
        self.name = name
        self.node_coord = validate_node_coord(node_coord, name)
        self.tile_coord = convert_tile_coord(node_coord, name)

    @staticmethod
    def parse_joints(data: dict) -> dict[Direction, list[TileJoint]]:
        joints_dict = {}

        for direction, joints in data.items():
            joints_list = [TileJoint(**joint) for joint in joints]
            joints_dict[Direction.from_str(direction)] = joints_list

        return joints_dict


@dataclass
class Tile:
    """
        Dataclass representing a tile (1000x1000mm). Each tile needs a unique tile id.
        It also has lists of the dataclasses 'TileNode' and 'TilePath' as well as
        a dict mapping directions to a list of the dataclass 'TileJoint'.
        More information on tiles can be found in the documentation.
    """

    tile_id: str
    joints: dict[Direction, list[TileJoint]]
    nodes: list[TileNode] = field(default_factory=list)
    paths: list[TilePath] = field(default_factory=list)

    @staticmethod
    def as_base_tile(data: dict) -> Tile:
        """
        Creates a base tile from the given json data dict. There can only be one base tile.
        It describes the joint positions of all tiles and has no nodes or paths of its own.
        """

        return Tile(tile_id="base_tile", joints=TileJoint.parse_joints(data['joints']), nodes=list(), paths=list())

    @staticmethod
    def from_json_dict(data: dict, base_tile: Tile, tile_id: str) -> Tile:
        """
        Creates a tile from the given json data dict with the unique given tile id.
        The tile inherits the joint positions of the given base_tile.
        """

        # PARSING
        paths = [TilePath(from_=path['from'], to_=path['to']) for path in data['paths']]
        nodes = [TileNode(name=node['name'], node_coord=node['node_coord']) for node in data['nodes']]
        joints = base_tile.joints

        validate(nodes, joints, paths)
        return Tile(tile_id=tile_id, joints=joints, nodes=nodes, paths=paths)


def validate(nodes: list[TileNode], joints: dict[Direction, list[TileJoint]], paths: list[TilePath]):
    """
    Validates the given nodes, joints and paths for reference and formatting consistency.
    Raises an error if the validation fails.
    """

    # No duplicate nodes
    node_names: set[str] = set()
    node_coords: set[tuple[float, float]] = set()
    for node in nodes:
        if node.name in node_names:
            raise ValueError(f"There can not be two nodes with the name {node.name}")
        node_names.add(node.name)

        if (node.node_coord.x, node.node_coord.y) in node_coords:
            raise ValueError(f"There can not be two nodes with the node coord {node.node_coord}")
        node_coords.add((node.node_coord.x, node.node_coord.y))

    # No duplicate paths
    path_origins: set[str] = set()
    for path in paths:
        if path.from_ in path_origins:
            raise ValueError(f"There can not be multiple paths connected to {path.from_}")
        if path.to_ in path_origins:
            raise ValueError(f"There can not be multiple paths connected to {path.to_}")

        # Only add after testing to ignore paths that loop back to the same node exit
        path_origins.add(path.from_)
        path_origins.add(path.to_)

    # Validation for from_ and to_ in paths
    joint_names = {joint.name for joints_list in joints.values() for joint in joints_list}
    dir_abbreviations = {direction.abbreviation() for direction in Direction.real_directions_ordered()}
    for path in paths:
        validate_path_point(path, path.from_, node_names, joint_names, dir_abbreviations)
        validate_path_point(path, path.from_, node_names, joint_names, dir_abbreviations)


def validate_path_point(path: TilePath, point_id: str,
                        node_names: set[str], joint_names: set[str], dir_abbreviations: set[str]):
    """
    Validates a single path point (from or to) in the given path for reference and formatting consistency.
    Raises an error if the validation fails.
    """

    split = point_id.split(':')
    if not (
            split[0] in node_names and len(split) == 2 and split[1] in dir_abbreviations
    ) and point_id not in joint_names:
        raise ValueError(
            f"Invalid reference in path {path.name}: {point_id}")


def validate_node_coord(coord: list[float], parent_id: str) -> Vector2:
    """
    Takes the given float list coordinate and, if valid, converts it to a Vector2 and returns it.
    Raises a ValueError otherwise
    """

    if coord[0] < 0 or coord[0] > 4 or coord[1] < 0 or coord[1] > 4:
        raise ValueError(f"{parent_id}: node coord {coord} is outside of the range ([0,4], [0,4])")

    if (coord[0] == 4 and coord[1] == 4) or (coord[0] == 0 and coord[1] == 0) or \
            (coord[0] == 0 and coord[1] == 4) or (coord[0] == 4 and coord[1] == 0):
        raise ValueError(f"{parent_id}: node coord {coord} is in a corner and therefore invalid")

    if "joint" not in parent_id:
        if coord[0] == 0 or coord[0] == 4 or coord[1] == 0 or coord[1] == 4:
            raise ValueError(f"{parent_id}: {coord} is invalid. Only joints be on the tile edge")

    return Vector2(coord[0], coord[1])


node_coord_to_tile_coord: dict[float, float] = {
    0: 0, 1: 120, 2: 500, 3: 880, 4: 1000
}


def convert_tile_coord(coord: list[float], parent_id: str) -> Vector2:
    """
    Converts the given node coordinate to a tile coordinate in mm.
    """

    x = node_coord_to_tile_coord.get(coord[0])
    y = node_coord_to_tile_coord.get(coord[1])

    if x is None or y is None:
        raise ValueError(f"{parent_id}: Cannot parse node coord {coord} to tile coord")

    return Vector2(x, y)
