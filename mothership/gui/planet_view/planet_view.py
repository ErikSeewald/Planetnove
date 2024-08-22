from __future__ import annotations
import sys
from enum import Enum
from typing import Optional
import pygame
from pygame.math import Vector2
from mothership.gui.planet_view import planet_parser, joint_attacher
from mothership.gui.planet_view.tile import DraggableTile
from mothership.mothership import Mothership
from planets.code.planet import Planet
from planets.code.tile_data import Tile
from util.direction import Direction


class PlanetView:
    """
    Class handling the mothership planet view.
    """

    # PYGAME
    screen: pygame.surface

    # TILES
    draggable_tiles: list[DraggableTile]
    dragged_tile: Optional[DraggableTile]
    tile_data: list[Tile]

    # PLANET
    planet: Optional[Planet]

    # MOTHERSHIP
    mothership: Mothership

    # STATE
    is_dragging_screen: bool
    last_mouse_pos: Vector2

    class Mode(Enum):
        EDIT = 1
        PLANET = 2
    mode: Mode

    # EVENTS
    sub_gui_outdated: bool

    def __init__(self, draggable_tiles: list[DraggableTile], tile_data: list[Tile], mothership: Mothership):
        self.mothership = mothership

        # PYGAME
        pygame.init()
        self.screen = pygame.display.set_mode((1400, 800), pygame.RESIZABLE)
        pygame.display.set_caption("Planet view")

        # PLANET TILES
        self.draggable_tiles = draggable_tiles
        self.dragged_tile = None
        self.tile_data = tile_data

        # PLANET
        self.planet = None

        # STATE
        self.is_dragging_screen = False
        self.last_mouse_pos = Vector2(0, 0)
        self.mode = self.Mode.EDIT

        # EVENTS
        self.sub_gui_outdated = False

    def update(self):
        self.handle_events()
        self.render()
        pygame.display.flip()

    def handle_events(self):
        events: list[pygame.event.Event] = pygame.event.get()
        for event in events:
            # QUIT
            if event.type == pygame.QUIT:
                sys.exit()

            # KEY EVENTS
            if event.type == pygame.KEYDOWN:
                # BLANK MODE
                if event.key == pygame.K_b:
                    for tile in self.draggable_tiles:
                        tile.set_blank_mode(not tile.blank_mode)

                # TODO: Remove this debug stuff
                if event.key == pygame.K_w:
                    self.mothership.planet_manager.tank.departure_direction = Direction.NORTH
                    self.mothership.planet_manager.on_tank_arrival()

                elif event.key == pygame.K_a:
                    self.mothership.planet_manager.tank.departure_direction = Direction.WEST
                    self.mothership.planet_manager.on_tank_arrival()

                elif event.key == pygame.K_s:
                    self.mothership.planet_manager.tank.departure_direction = Direction.SOUTH
                    self.mothership.planet_manager.on_tank_arrival()

                elif event.key == pygame.K_d:
                    self.mothership.planet_manager.tank.departure_direction = Direction.EAST
                    self.mothership.planet_manager.on_tank_arrival()
            # SCREEN DRAG
            self.drag_screen(event)

        if self.mode == self.Mode.EDIT:
            self.handle_events_edit_mode(events)
        elif self.mode == self.Mode.PLANET:
            self.handle_events_planet_mode(events)

    def handle_events_edit_mode(self, events: list[pygame.event.Event]):
        for event in events:

            # KEY EVENTS
            if event.type == pygame.KEYDOWN:
                # ROTATE TILE
                if event.key == pygame.K_r:
                    for tile in self.draggable_tiles:
                        if tile.is_dragging:
                            tile.rotate_right()

            # TILE DRAG
            keys = pygame.key.get_pressed()
            if not keys[pygame.K_LSHIFT]:
                # reversed so the one drawn last is grabbed first
                for tile in self.draggable_tiles.__reversed__():
                    tile.handle_drag_event(event)
                    if tile.is_dragging:
                        self.dragged_tile = tile
                        break

                if self.dragged_tile is not None:
                    # GRABBED TILE
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        joint_attacher.detach_from_others(self.dragged_tile, self.draggable_tiles)
                        self.sub_gui_outdated = True

                    # RELEASED TILE
                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        self.attach_tiles()
                        self.dragged_tile = None
                        self.sub_gui_outdated = True

    def handle_events_planet_mode(self, events: list[pygame.event.Event]):
        pass

    def drag_screen(self, event):
        """
        Handle screen drag events. The screen gets dragged if
        A) the mouse wheel is pressed or B) shift and the left mouse button are pressed (laptops)
        """

        pressed_keys = pygame.key.get_pressed()

        # START DRAGGING
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 2 or (event.button == 1 and pressed_keys[pygame.K_LSHIFT]):
                self.is_dragging_screen = True
                self.last_mouse_pos = Vector2(event.pos[0], event.pos[1])

        # STOP DRAGGING
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2 or (event.button == 1 and pressed_keys[pygame.K_LSHIFT]):
                self.is_dragging_screen = False

        # DRAG
        elif event.type == pygame.MOUSEMOTION and self.is_dragging_screen:
            dx = event.pos[0] - self.last_mouse_pos.x
            dy = event.pos[1] - self.last_mouse_pos.y

            self.last_mouse_pos = Vector2(event.pos[0], event.pos[1])
            for tile in self.draggable_tiles:
                tile.rect = tile.rect.move(dx, dy)

    def render(self):
        # BACKGROUND
        self.screen.fill((25, 25, 25))

        # TILES
        for tile in self.draggable_tiles:
            if tile != self.dragged_tile:  # Draw all other tiles first
                tile.draw(self.screen)

        if self.dragged_tile:  # Draw dragged tile on top
            self.dragged_tile.draw(self.screen)

    def attach_tiles(self):
        for tile in self.draggable_tiles:
            joint_attacher.try_attach(tile, self.draggable_tiles)

    def finish_planet(self):
        if not self.can_finish_planet():
            return
        self.planet = planet_parser.parse_planet(self.draggable_tiles, self.tile_data)
        self.mothership.set_planet(self.planet) # TODO: Better way to do this?
        self.switch_mode(self.Mode.PLANET)

    def can_finish_planet(self) -> bool:
        if self.dragged_tile is not None:
            return False
        if self.mode != self.Mode.EDIT:
            return False
        return joint_attacher.all_tiles_form_one_planet(self.draggable_tiles)

    def can_switch_to_edit_mode(self) -> bool:
        if self.mode == self.Mode.PLANET:
            pass

        return True

    def switch_mode(self, new_mode: Mode):
        if self.mode == self.Mode.PLANET:
            if new_mode == self.Mode.EDIT:
                if self.can_switch_to_edit_mode():
                    self.mode = self.Mode.EDIT
            else:
                self.mode = new_mode

        elif self.mode == self.Mode.EDIT:
            if new_mode == self.Mode.PLANET:
                if self.planet is not None:
                    self.mode = self.Mode.PLANET
            else:
                self.mode = new_mode

    def register_sub_gui_update(self):
        self.sub_gui_outdated = False
