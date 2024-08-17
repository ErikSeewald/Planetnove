import os
import sys
import pygame
from pygame.math import Vector2
from mothership.gui.tile import DraggableTile
from mothership.io.load_planets import PlanetLoader
from util.direction import Direction


def main():
    pygame.init()

    # SCREEN
    screen: pygame.Surface = pygame.display.set_mode((1400, 1000))
    pygame.display.set_caption("Tile viewer")

    clock = pygame.time.Clock()

    planet_loader = PlanetLoader(os.path.join(os.getcwd(), "planets"))
    load_result = planet_loader.load()

    draggable_tiles: list[DraggableTile]
    if load_result.is_success():
        draggable_tiles = planet_loader.svg_tiles
    else:
        print(f"Failed to load planet files: {load_result.message}")
        return 1

    is_dragging_screen = False
    last_mouse_pos = (0, 0)

    while True:
        screen.fill((20, 20, 20))

        for tile in draggable_tiles:
            if tile.waiting_to_attach:
                try_attach(tile, draggable_tiles)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b:
                    for tile in draggable_tiles:
                        tile.set_blank_mode(not tile.blank_mode)

                if event.key == pygame.K_r:
                    for tile in draggable_tiles:
                        if tile.is_dragging:
                            tile.rotate_right()

            # Handle screen dragging
            is_dragging_screen, last_mouse_pos = drag_screen(
                event, is_dragging_screen, last_mouse_pos, draggable_tiles
            )

            for tile in draggable_tiles.__reversed__():  # reversed so the one drawn last is grabbed first
                tile.detach_joints()  # TODO: Just detach the ones of the one being dragged from the others
                tile.handle_drag_event(event)
                if tile.is_dragging:
                    break  # Only allow one tile to be dragged at a time

        # RENDER
        for tile in draggable_tiles:
            # Adjust tile position by screen offset before drawing
            tile.draw(screen)

        pygame.display.flip()
        clock.tick(60)


def drag_screen(event, is_dragging_screen, last_mouse_pos, tiles):
    if event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 2:
            is_dragging_screen = True
            last_mouse_pos = event.pos

    elif event.type == pygame.MOUSEBUTTONUP:
        if event.button == 2:
            is_dragging_screen = False

    elif event.type == pygame.MOUSEMOTION:
        if is_dragging_screen:
            dx = event.pos[0] - last_mouse_pos[0]
            dy = event.pos[1] - last_mouse_pos[1]

            last_mouse_pos = event.pos

            for tile in tiles:
                tile.rect = tile.rect.move(dx, dy)

    return is_dragging_screen, last_mouse_pos


def try_attach(tile: DraggableTile, all_tiles: list[DraggableTile]):

    # Check every tile for joint connections
    for tile_b in all_tiles:
        if tile_b == tile:
            continue
        try_attach_single(tile, tile_b, all_tiles)
    tile.finish_attaching()


def try_attach_single(tile_a: DraggableTile, tile_b: DraggableTile, all_tiles: list[DraggableTile]):

    # IMPORTANT: Maintain nesting structure. Looping over the sides of both tiles in the outer loops
    # and the side joints in the inner loops allows for early returns if a side has been attached

    # SIDES OF TILE B
    for local_dir_b in tile_b.joints.keys():
        global_dir_b = tile_b.local_direction_to_global(local_dir_b)

        # SIDES OF TILE A
        for local_dir_a in tile_a.joints.keys():
            side_attached = False  # Have any attachments been made in this side loop?
            global_dir_a = tile_a.local_direction_to_global(local_dir_a)

            # JOINTS OF TILE B
            for joint_num_b in range(1, 4):
                if not tile_b.is_joint_free(local_dir_b, joint_num_b):
                    continue # Skip joints that already have other joints attached

                joint_pos_b = get_joint_pos(global_dir_b, tile_b, joint_num_b)

                # JOINTS OF TILE A
                for joint_num_a in range(1, 4):
                    if not tile_a.is_joint_free(local_dir_a, joint_num_a):
                        continue  # Skip joints that already have other joints attached

                    joint_pos_a = get_joint_pos(global_dir_a, tile_a, joint_num_a)

                    # Connect if the distance between joints is less than a 10th of the tile size
                    if joint_pos_a.distance_to(joint_pos_b) < tile_a.blank_image.get_height() / 10:

                        # Snapping and overlap check for both tile a and b
                        snap_offset = joint_pos_b - joint_pos_a
                        tile_a_moved = tile_a.rect.move(snap_offset)
                        overlap = False
                        for tile in all_tiles:
                            if tile != tile_a and tile_a_moved.colliderect(tile):
                                overlap = True
                            elif tile != tile_b and tile_b.rect.colliderect(tile):
                                overlap = True

                        # Do not attach if the resulting snapped position would result in two tiles overlapping
                        if overlap:
                            break

                        tile_a.snap_to_pos(tile_a.rect.x + snap_offset.x, tile_a.rect.y + snap_offset.y)
                        tile_b.snapped_in_place = True

                        # Attach
                        tile_a.attach_joint(local_dir_a, joint_num_a,
                                            tile_b.tile_id + "_joint_" + local_dir_b.abbreviation() + str(joint_num_b))
                        side_attached = True
                        break

            # If this loop attached joints on this side already and then finished the side,
            # there can be no more attachments on other sides between tile_a and tile_b -> return early
            if side_attached:
                return


def get_joint_pos(direction: Direction, tile: DraggableTile, joint_num: int) -> Vector2:
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
