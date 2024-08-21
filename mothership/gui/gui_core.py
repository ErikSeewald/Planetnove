from __future__ import annotations
import pygame
from mothership.gui.planet_view.planet_view import PlanetView
from mothership.gui.planet_view.planet_view_subgui import PlanetViewSubGUI
from mothership.gui.planet_view.tile import DraggableTile
from mothership.gui.sub_gui import SubGUI
from planets.code.tile_data import Tile
import dearpygui.dearpygui as dpg


class GUICore:
    """
    Core class handling the GUI loop of the mothership.
    """

    # PYGAME
    clock: pygame.time.Clock

    # PLANET VIEW
    planet_view: PlanetView

    # DEARPYGUI
    sub_GUIs: list[SubGUI]

    def __init__(self, draggable_tiles: list[DraggableTile], tile_data: list[Tile]):

        # PYGAME
        self.clock = pygame.time.Clock()

        # PLANET VIEW
        self.planet_view = PlanetView(draggable_tiles, tile_data)

        # DEARPYGUI
        dpg.create_context()

        self.sub_GUIs = [
            PlanetViewSubGUI("planet_view", gui_core=self, planet_view=self.planet_view),
        ]

        dpg.create_viewport(title='Mothership', width=1400, height=850)
        dpg.set_viewport_clear_color([20, 20, 20, 255])
        dpg.setup_dearpygui()
        dpg.show_viewport()

    def loop(self):
        while dpg.is_dearpygui_running():

            # PLANET VIEW
            self.planet_view.update()

            # DEARPYGUI
            dpg.render_dearpygui_frame()
            for gui in self.sub_GUIs:
                gui.update()

            self.clock.tick(60)
