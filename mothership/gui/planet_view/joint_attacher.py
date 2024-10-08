from collections import deque

from pygame import Vector2
from mothership.gui.planet_view.tile import DraggableTile
from util.direction import Direction


def try_attach(tile: DraggableTile, all_tiles: list[DraggableTile]):
    """
    Tries to find potential joint matches between the given tile and the given list of all tiles
    and attaches them together.
    ('tile' is allowed to be included in 'all_tiles'. This function makes sure no tile is attached to itself)
    :param tile: The tile to attach to the others.
    :param all_tiles: The list of all potential attachment partners.
    """

    # Skip calculation if the given tile is also the only tile
    if len(all_tiles) == 1 and tile == all_tiles[0]:
        tile.snapped_in_place = True
        return

    # Check every tile for joint connections
    for tile_b in all_tiles:
        if tile_b == tile:
            continue
        try_attach_single(tile, tile_b, all_tiles)


def try_attach_single(tile_a: DraggableTile, tile_b: DraggableTile, all_tiles: list[DraggableTile]):
    """
    Tries to attach tile_a to a single other tile_b. Uses information about the layout of all tiles to
    calculate attachment parameters.
    """

    # IMPORTANT: Maintain nesting structure. Looping over the sides of both tiles in the outer loops
    # and the side joints in the inner loops allows for early returns if a side has been attached.
    # Also keep in mind that this code was originally intended to allow for attachments of less than three joints
    # per side. This functionality returns if you remove the skip_side check.

    # SIDES OF TILE B
    for local_dir_b in tile_b.joints.keys():
        global_dir_b = tile_b.local_direction_to_global(local_dir_b)

        # SIDES OF TILE A
        for local_dir_a in tile_a.joints.keys():
            side_attached = False  # Have any attachments been made in this side loop?
            global_dir_a = tile_a.local_direction_to_global(local_dir_a)

            # For both joints, loop over the center joints with joint_num=2 first. If a2 and b2 cannot
            # be attached, skip this side because we only want attachments of all 3 joints and the center joints
            # are not dependent on ordering
            skip_side = False

            # JOINTS OF TILE B
            for joint_num_b in [2, 1, 3]:
                if not tile_b.is_joint_free(local_dir_b, joint_num_b):
                    continue # Skip joints that already have other joints attached

                joint_pos_b = get_joint_pos(tile_b, global_dir_b, joint_num_b)

                # JOINTS OF TILE A
                for joint_num_a in [2, 1, 3]:
                    if not tile_a.is_joint_free(local_dir_a, joint_num_a):
                        continue  # Skip joints that already have other joints attached

                    joint_pos_a = get_joint_pos(tile_a, global_dir_a, joint_num_a)
                    distance = joint_pos_a.distance_to(joint_pos_b)
                    tile_size = tile_a.blank_image.get_height()

                    # Connect if the distance between joints is less than a 10th of the tile size.
                    # And if the tile has already snapped to another, the distance needs to be almost zero
                    # to avoid cascading snapping.
                    if (not tile_a.snapped_in_place and distance < tile_size / 10) or distance < 1:

                        # SNAP OFFSET
                        snap_offset = joint_pos_b - joint_pos_a
                        if would_overlap(tile_a, tile_b, all_tiles, snap_offset):
                            break

                        if not tile_a.snapped_in_place: # Avoid cascading snapping
                            tile_a.snap_to_pos(tile_a.rect.x + snap_offset.x, tile_a.rect.y + snap_offset.y)
                            tile_b.snapped_in_place = True

                        # Attach
                        tile_a.attach_joint(local_dir_a, joint_num_a,
                                            tile_b.tile_id + "_joint_" + local_dir_b.abbreviation() + str(joint_num_b))
                        tile_b.attach_joint(local_dir_b, joint_num_b,
                                            tile_a.tile_id + "_joint_" + local_dir_a.abbreviation() + str(joint_num_a))
                        side_attached = True
                        break

                    elif joint_num_a == 2 and joint_num_b == 2:
                        skip_side = True
                        break

                if skip_side:
                    break

            # If this loop attached joints on this side already then there can be no more attachments
            # on other sides between tile_a and tile_b -> return early
            if side_attached:
                return


def would_overlap(tile_a: DraggableTile, tile_b: DraggableTile, all_tiles: list[DraggableTile], snap_offset: Vector2):
    """
    :return: Whether snapping tile_a to tile_b with the given snap offset would result in any tiles overlapping.
    """

    tile_a_moved = tile_a.rect.move(snap_offset)
    for tile in all_tiles:
        if tile != tile_a and tile_a_moved.colliderect(tile):
            return True

        # Extra condition snapped_in_places only here, otherwise tile_a-tile_b collision can not be detected if
        # they are both not snapped into place yet.
        elif tile != tile_b and tile.snapped_in_place and tile_b.rect.colliderect(tile):
            return True
    return False


def get_joint_pos(tile: DraggableTile, direction: Direction, joint_num: int) -> Vector2:
    """
    Gets the screen coordinates of the given tile's joint at the given global direction and joint number.
    Considers translation and rotation of the tile.
    (Note: Joint number follows the project rules -> counting up from SOUTH to NORTH and WEST to EAST relative
    to the tile. This means the global joint number ordering can be different based on tile rotation)
    """

    tile_size = tile.blank_image.get_height()
    joint_pos = Vector2(tile.rect.x, tile.rect.y)

    # Adjust joint num for joint offset based on rotation to match ordering pre rotation
    # (counting up towards north and east)
    if tile.rotation_deg == 0 and direction.value % 180 == 90 or \
            tile.rotation_deg == 180 and direction.value % 180 == 0 or \
            tile.rotation_deg == 270:
        joint_num_adjusted = 4 - joint_num # inverse ordering
    else:
        joint_num_adjusted = joint_num

    # JOINT OFFSET
    joint_offset: float
    if joint_num_adjusted == 1:
        joint_offset = tile_size * 12/100
    elif joint_num_adjusted == 2:
        joint_offset = tile_size / 2
    else:
        joint_offset = tile_size - tile_size * 12/100

    # DIRECTION BASED COORDINATES
    if direction == Direction.NORTH:
        joint_pos.x += joint_offset

    elif direction == Direction.EAST:
        joint_pos.x += tile_size
        joint_pos.y += joint_offset

    elif direction == Direction.SOUTH:
        joint_pos.x += joint_offset
        joint_pos.y += tile_size

    elif direction == Direction.WEST:
        joint_pos.y += joint_offset

    return joint_pos


def detach_from_others(tile: DraggableTile, all_tiles: list[DraggableTile]):
    """
    Detaches the given tile from the other tiles.
    """

    for tile_b in all_tiles:
        if tile_b == tile:
            continue

        for direction_b in tile_b.joints.keys():
            for joint_num_b in range(1, 4):
                if tile.tile_id in tile_b.joints.get(direction_b)[joint_num_b - 1]:
                    tile_b.detach_joint(direction_b, joint_num_b)


def all_tiles_form_one_planet(all_tiles: list[DraggableTile]) -> bool:
    """
    Returns whether the given list of tiles is fully connected into a single planet and not multiple
    different planets.
    """

    # Skip calculation if there is only one tile
    if len(all_tiles) == 1 and all_tiles[0].snapped_in_place:
        return True

    # Begin with one tile and try to reach all tiles from it -> Success: return True
    id_to_tile: dict[str, DraggableTile] = {t.tile_id: t for t in all_tiles}
    reached_tile_ids: set[str] = set()
    tile_stack: deque[DraggableTile] = deque()
    tile_stack.append(all_tiles[0])

    while tile_stack:
        if len(reached_tile_ids) == len(id_to_tile):
            return True

        cur_tile = tile_stack.pop()
        for direction in cur_tile.joints.keys():
            connected_tile_id = cur_tile.joints.get(direction)[0].split("_joint")[0]
            if connected_tile_id != "None" and connected_tile_id not in reached_tile_ids:
                tile_stack.append(id_to_tile.get(connected_tile_id))
                reached_tile_ids.add(connected_tile_id)
    return False
