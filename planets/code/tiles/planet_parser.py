from pygame import Vector2
from mothership.gui.planet_view.draggable_tile import DraggableTile
from planets.code.node import Node
from planets.code.path import Path
from planets.code.planet import Planet
from planets.code.tiles.tile_data import Tile, TileMeasure
from util.direction import Direction


def parse_planet(draggable_tiles: list[DraggableTile], tile_data: list[Tile]) -> Planet:
    """
    Parses the given set of draggable tiles and the corresponding tile data into a planet with a single coordinate
    system and no joints in between.
    In doing so it also maps all local direction data to global directions.
    """

    # Mapping tile ids to their data and draggable representations
    tile_values: dict[str, tuple[DraggableTile, Tile]] = dict()
    draggable_dict = {t.tile_id: t for t in draggable_tiles}
    for tile in tile_data:
        tile_values[tile.tile_id] = (draggable_dict[tile.tile_id], tile)

    nodes = parse_nodes(tile_values)
    paths = parse_paths(tile_values, nodes)
    return Planet(nodes, paths)


def parse_nodes(tile_data: dict[str, tuple[DraggableTile, Tile]]) -> dict[str, Node]:
    """
    Parses the given tile_data into a dict mapping node IDs to nodes and calculates their global node coordinates
    based on tile connections.
    """

    nodes: dict[str, Node] = dict()

    # COORDINATE OFFSETS
    tile_coord_offsets: dict[str, tuple[float, float]] = dict()

    # Because all tiles are squares and connected -> find tile with the highest y coordinate (lowest on screen)
    # and use that tiles origin as the planet coordinate origin. All other tiles receive coordinate offsets
    # based on their connection to the lowest tile.
    origin_tile = max(tile_data.values(), key=lambda value: value[0].rect.y)
    size_mm = TileMeasure.tile_size_mm
    for tile_id, tile in tile_data.items():
        x_offset = (tile[0].rect.x - origin_tile[0].rect.x) * (size_mm / tile[0].rect.width)
        y_offset = (origin_tile[0].rect.y - tile[0].rect.y) * (size_mm / tile[0].rect.height)
        tile_coord_offsets[tile_id] = node_offset(x_offset), node_offset(y_offset)

    # NODES
    for tile_id, tile in tile_data.items():
        coord_offset = tile_coord_offsets.get(tile_id)
        for node in tile[1].nodes:
            # COORD
            coord = Vector2(node.node_coord.x, node.node_coord.y)

            # Match draggable tile rotation
            coord = rotate_coord(coord, center=Vector2(2, 2), rotation_deg=-tile[0].rotation_deg)

            # Positional offset
            coord.x += coord_offset[0]
            coord.y += coord_offset[1]

            # Paths get added to the nodes in the parse_paths() function
            nodes[node.name] = Node(node_id=node.name, coord=coord)

    return nodes


def node_offset(tile_offset: float) -> float:
    """
    :return: The node coord offset based on the given tile coord offset
    """

    return int(tile_offset / TileMeasure.tile_size_mm) * 3


def rotate_coord(coord: Vector2, center: Vector2, rotation_deg: int) -> Vector2:
    """
    Rotates the given coordinate around the given center by the given amount of degrees and returns the result.
    """

    translated_vector = coord - center
    rotated_vector = translated_vector.rotate(rotation_deg)
    return rotated_vector + center


def parse_paths(tile_data: dict[str, tuple[DraggableTile, Tile]], nodes: dict[str, Node]) -> dict[str, Path]:
    """
    Parses the given tile_data into a dict mapping path IDs to paths and updates the given nodes with the path IDs
    at the correct global directions.
    Thereby it also connects nodes that were connected between tiles through joints and removes paths that lead to
    joints that do not have another tile node connected to them.
    """

    paths: dict[str, Path] = dict()

    for tile_id, tile in tile_data.items():
        for path in tile[1].paths:
            # Do not consider joint to joint paths here (only consider them in parse_path_node())
            # Otherwise it would break the use of tile.rotation_deg
            if "joint" in path.from_ and "joint" in path.to_:
                continue

            # PATH NODE IDs
            node_a: str = parse_path_node(path.from_, tile_id, tile_data)
            node_b: str = parse_path_node(path.to_, tile_id, tile_data)
            if node_a == "None" or node_b == "None":
                continue  # Do not add paths that do not connect two nodes

            # DRAG TILE ROTATION
            split_a = node_a.split(":")
            drag_tile_a = tile[0]
            direction_a = Direction.rotated(Direction.from_str(split_a[1]), drag_tile_a.rotation_deg)
            id_dir_key_a = Node.id_direction_key(split_a[0], direction_a)

            split_b = node_b.split(":")
            drag_tile_b = tile_data.get(get_tile_id(split_b[0], tile_data))[0]
            direction_b = Direction.rotated(Direction.from_str(split_b[1]), drag_tile_b.rotation_deg)
            id_dir_key_b = Node.id_direction_key(split_b[0], direction_b)

            # Only add path if it has not already been added from the other direction
            inverse_path_id = Path.id_from_node_keys(id_dir_key_b, id_dir_key_a)
            if paths.get(inverse_path_id) is not None:
                continue

            path = Path(id_dir_key_a, id_dir_key_b)
            paths[path.id] = path

            # ADD PATH TO NODES
            nodes.get(split_a[0]).set_path(direction_a, path.id)
            nodes.get(split_b[0]).set_path(direction_b, path.id)

    return paths


def parse_path_node(node_id: str, tile_id: str, tile_data: dict[str, tuple[DraggableTile, Tile]]) -> str:
    """
    Takes the given node_id and parses it to a valid node.
    If the node_id is already valid, it is simply returned. If it is a joint id, then the function will find
    the node that joint is connected to and return it.
    """

    if "joint" not in node_id:
        return node_id

    # JOINT
    split = node_id.split("_")
    joint_side = Direction.from_str(split[1][0])
    joint_num = int(split[1][1])

    # What node is the joint connected to on the other tile
    connected_joint = tile_data[tile_id][0].joints.get(joint_side)[joint_num - 1]
    connected_tile = tile_data.get(connected_joint.split("_joint")[0])

    if connected_tile is None:
        return "None"

    # Find the connected node, or leave it as 'None' if no node is connected.
    # If another joint is connected, find the node recursively.
    node_b = "None"
    connected_joint_id = "joint" + connected_joint.split("_joint")[1]
    for path in connected_tile[1].paths:
        # CONNECTED TO 'TO'
        if path.to_ == connected_joint_id:
            if "joint" not in path.from_:
                node_b = path.from_
            else:
                node_b = parse_path_node(path.from_, connected_tile[1].tile_id, tile_data)
            break

        # CONNECTED TO 'FROM'
        elif path.from_ == connected_joint_id:
            if "joint" not in path.to_:
                node_b = path.to_
            else:
                node_b = parse_path_node(path.to_, connected_tile[1].tile_id, tile_data)
            break

    return node_b


def get_tile_id(node_id: str, tile_data: dict[str, tuple[DraggableTile, Tile]]) -> str:
    """
    Gets the name of the tile which the given node id belongs to.
    """

    for tile in tile_data.values():
        for node in tile[1].nodes:
            if node_id == node.name:
                return tile[1].tile_id
    return "None"
