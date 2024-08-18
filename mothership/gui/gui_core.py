from __future__ import annotations
from typing import Optional
import pygame
from pygame.math import Vector2
from mothership.gui import joint_attacher
from mothership.gui.tile import DraggableTile


class GUICore:
    """
    Core class handling the gui loop of the mothership tile viewer.
    """

    # PYGAME
    screen: pygame.surface
    clock: pygame.time.Clock

    # TILES
    draggable_tiles: list[DraggableTile]
    dragged_tile: Optional[DraggableTile]

    # STATE
    is_dragging_screen: bool
    last_mouse_pos: Vector2
    is_exiting: bool

    def __init__(self, draggable_tiles: list[DraggableTile]):
        # PYGAME
        pygame.init()
        self.screen = pygame.display.set_mode((1400, 800), pygame.RESIZABLE)
        pygame.display.set_caption("Tile viewer")
        self.clock = pygame.time.Clock()

        # PLANET TILES
        self.draggable_tiles = draggable_tiles
        self.dragged_tile = None

        # STATE
        self.is_dragging_screen = False
        self.last_mouse_pos = Vector2(0, 0)
        self.is_exiting = False

    def loop(self):
        """
        The main gui loop. Handles rendering, updating and the pygame clock.
        """

        while True:
            self.update_tiles()
            self.handle_events()
            if self.is_exiting:
                return

            self.render()
            pygame.display.flip()
            self.clock.tick(60)

    def update_tiles(self):
        for tile in self.draggable_tiles:
            if tile.waiting_to_attach:
                joint_attacher.try_attach(tile, self.draggable_tiles)

    def handle_events(self):
        for event in pygame.event.get():

            # QUIT
            if event.type == pygame.QUIT:
                self.is_exiting = True
                return

            # KEY EVENTS
            keys = pygame.key.get_pressed()
            if event.type == pygame.KEYDOWN:
                # BLANK MODE
                if event.key == pygame.K_b:
                    for tile in self.draggable_tiles:
                        tile.set_blank_mode(not tile.blank_mode)

                # ROTATE TILE
                if event.key == pygame.K_r:
                    for tile in self.draggable_tiles:
                        if tile.is_dragging:
                            tile.rotate_right()

            # SCREEN DRAG
            self.drag_screen(event)

            # TILE DRAG
            if not keys[pygame.K_LSHIFT]:

                # reversed so the one drawn last is grabbed first
                for tile in self.draggable_tiles.__reversed__():
                    tile.handle_drag_event(event)
                    if tile.is_dragging:
                        joint_attacher.detach_from_others(tile, self.draggable_tiles)
                        self.dragged_tile = tile
                        break

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
        self.screen.fill((20, 20, 20))

        # TILES
        for tile in self.draggable_tiles:
            if tile != self.dragged_tile:  # Draw all other tiles first
                tile.draw(self.screen)

        if self.dragged_tile:  # Draw dragged tile on top
            self.dragged_tile.draw(self.screen)
