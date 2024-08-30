from typing import Optional
import pygame

from mothership.gui.tank_internal_map.tank_map_renderer import TankMapRenderer
from mothership.gui.tank_internal_map.tank_map_subgui import TankMapSubGUI
from mothership.gui.update_event import UpdateEvent
from mothership.gui.planet_view.planet_view import PlanetView
from mothership.gui.planet_view.planet_view_subgui import PlanetViewSubGUI
from mothership.gui.planet_view.tile import DraggableTile
from mothership.gui.coms_subgui.coms_subgui import ComsSubGUI
from mothership.gui.sub_gui import SubGUI
from mothership.io.communications import Communications
from planets.code.tile_data import Tile
import dearpygui.dearpygui as dpg

from util.direction import Direction


class GUICore:
    """
    Core class handling the GUI loop of the mothership.
    """

    # PLANET VIEW
    planet_view: PlanetView

    # DEARPYGUI
    sub_GUIs: dict[str, SubGUI] # window tag to SubGui

    # COMS
    coms: Communications

    def __init__(self, draggable_tiles: list[DraggableTile], tile_data: list[Tile], coms: Communications):
        pygame.init()
        self.planet_view = PlanetView(draggable_tiles, tile_data)

        # COMS
        self.coms = coms

        # DEARPYGUI
        dpg.create_context()

        self.sub_GUIs = {
            "planet_view": PlanetViewSubGUI("planet_view", gui_core=self, planet_view=self.planet_view),
            "coms": ComsSubGUI("coms", gui_core=self, coms=self.coms),
            "tank_map": TankMapSubGUI("tank_map", gui_core=self)
        }

        dpg.create_viewport(title='Mothership', width=1100, height=770)
        dpg.set_viewport_clear_color([20, 20, 20, 255])
        dpg.setup_dearpygui()
        dpg.show_viewport()

    def update(self) -> list[UpdateEvent]:
        events: list[UpdateEvent] = list()

        # PLANET VIEW
        pv_events = self.planet_view.update()
        events.extend(pv_events)

        # DEARPYGUI
        dpg.render_dearpygui_frame()
        for gui in self.sub_GUIs.values():
            events.extend(gui.update())

        return events

    def get_planet_view_mode(self) -> PlanetView.Mode:
        return self.planet_view.mode

    def is_start_pos_locked(self) -> bool:
        return self.sub_GUIs.get("planet_view").start_pos_locked

    def get_start_pos(self) -> Optional[tuple[str, Direction]]:
        planet_view_gui = self.sub_GUIs.get("planet_view")
        return planet_view_gui.start_node_id, planet_view_gui.start_direction

    def can_switch_to_edit_mode(self) -> bool:
        return self.sub_GUIs.get("coms").tank_header_state == ComsSubGUI.TankHeaderState.ADDING_TANK

    def tank_start_message_callback(self):
        self.coms.send_tank_start_message()
        self.sub_GUIs.get("coms").switch_to_mode_started()

    # TODO: Remove
    def add_planet_DEBUG(self, planet):
        self.sub_GUIs.get("tank_map").load_image(TankMapRenderer.render_map_image(planet))


