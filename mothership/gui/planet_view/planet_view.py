from __future__ import annotations
import sys
from enum import Enum
from typing import Optional
import pygame
from pygame.math import Vector2
from mothership.gui.planet_view import joint_attacher
from planets.code.parsing import planet_parser
from mothership.gui.planet_view.tile import DraggableTile
from mothership.update_event import UpdateEvent, SwitchedToPlanetMode, TileGrabbed, TileReleased
from planets.code.planet import Planet
from planets.code.parsing.tile_data import Tile


class PlanetView:
    """
    Class handling the mothership planet view.
    Responsible for editing and viewing the planet map.
    """

    # PYGAME
    screen: pygame.surface

    # TILES
    draggable_tiles: list[DraggableTile]
    dragged_tile: Optional[DraggableTile]
    tile_data: list[Tile]

    # PLANET
    planet: Optional[Planet]

    # STATE
    is_dragging_screen: bool
    last_mouse_pos: Vector2

    class Mode(Enum):
        EDIT = 1
        PLANET = 2
    mode: Mode

    # EVENTS
    update_events: list[UpdateEvent]
    planet_mode_switch_scheduled: bool

    def __init__(self, draggable_tiles: list[DraggableTile], tile_data: list[Tile]):
        # PYGAME
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
        self.update_events = list()
        self.planet_mode_switch_scheduled = False

    def update(self) -> list[UpdateEvent]:
        """
        Updates the planet view and returns a list of update events that occurred.
        """

        self.update_events.clear()

        self.mode_update()
        self.handle_events()
        self.render()
        pygame.display.flip()

        return self.update_events.copy()

    def mode_update(self):
        """
        Updates the planet views mode to planet mode if a switch is scheduled.
        """

        if self.planet_mode_switch_scheduled:
            self.planet = planet_parser.parse_planet(self.draggable_tiles, self.tile_data)
            self.update_events.append(SwitchedToPlanetMode(new_planet=self.planet))
            self.switch_mode(self.Mode.PLANET)
            self.planet_mode_switch_scheduled = False

    def handle_events(self):
        """
        Handles all pygame events and stores any update events that occur.
        """

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

            # SCREEN DRAG
            self.drag_screen(event)

        if self.mode == self.Mode.EDIT:
            self.handle_events_edit_mode(events)
        elif self.mode == self.Mode.PLANET:
            self.handle_events_planet_mode(events)

    def handle_events_edit_mode(self, events: list[pygame.event.Event]):
        """
        Handles pygame events specific to the edit mode.
        Stores any update events that occur.
        """

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
                        self.update_events.append(TileGrabbed())

                    # RELEASED TILE
                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        joint_attacher.try_attach(self.dragged_tile, self.draggable_tiles)
                        self.dragged_tile = None
                        self.update_events.append(TileReleased())

    def handle_events_planet_mode(self, events: list[pygame.event.Event]):
        """
        Handles pygame events specific to the planet mode.
        Stores any update events that occur.
        """

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
        """
        Renders the planet view using pygame.
        """

        # BACKGROUND
        self.screen.fill((25, 25, 25))

        # TILES
        is_planet_mode = self.mode == self.Mode.PLANET
        for tile in self.draggable_tiles:
            if tile != self.dragged_tile:  # Draw all other tiles first
                tile.draw(self.screen, is_planet_mode)

        if self.dragged_tile:  # Draw dragged tile on top
            self.dragged_tile.draw(self.screen, is_planet_mode)

    def finish_planet(self):
        """
        Schedules a planet mode switch for the next update, provided that can_finish_planet() is true.
        """

        if not self.can_finish_planet():
            return

        # Schedule instead of doing it here so that it can be added to the update events
        self.planet_mode_switch_scheduled = True

    def can_finish_planet(self) -> bool:
        """
        Returns whether edit mode can parse and finish the planet that is currently being edited.
        """

        if self.dragged_tile is not None:
            return False
        if self.mode != self.Mode.EDIT:
            return False
        return joint_attacher.all_tiles_form_one_planet(self.draggable_tiles)

    def switch_mode(self, new_mode: Mode) -> bool:
        """
        Switches the mode of the planet view. Never switch the mode manually.
        Returns whether the switch was successful.
        """

        if self.mode == new_mode:
            return True

        if self.mode == self.Mode.PLANET:
            self.mode = new_mode
            return True

        elif self.mode == self.Mode.EDIT:
            if new_mode == self.Mode.PLANET and self.planet is not None:
                self.mode = self.Mode.PLANET
                return True

        return False
