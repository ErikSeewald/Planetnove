from typing import Optional
import pygame
from mothership.gui.tank_internal_map.tank_map_renderer import TankMapRenderer
from mothership.gui.tank_internal_map.tank_map_subgui import TankMapSubGUI
from mothership.update_event import UpdateEvent, TankPlanetUpdate
from mothership.gui.planet_view.planet_view import PlanetView
from mothership.gui.planet_view.planet_view_subgui import PlanetViewSubGUI
from mothership.gui.planet_view.tile import DraggableTile
from mothership.gui.coms_subgui.coms_subgui import ComsSubGUI
from mothership.gui.sub_gui import SubGUI
from mothership.io.communications import Communications
from planets.code.planet import Planet
from planets.code.parsing.tile_data import Tile
import dearpygui.dearpygui as dpg

from planets.code.route import Route
from util.direction import Direction


class GUICore:
    """
    Core class handling the GUI loop of the mothership.
    Handles communication between all SubGUIs and other mothership submodules.
    """

    planet_view: PlanetView
    sub_GUIs: dict[str, SubGUI] # window tag to SubGui
    coms: Communications

    def __init__(self, draggable_tiles: list[DraggableTile], tile_data: list[Tile], coms: Communications):
        pygame.init()
        dpg.create_context()

        self.planet_view = PlanetView(draggable_tiles, tile_data)
        self.coms = coms

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
        """
        Updates the mothership's GUI and returns a list of all update events that occured.
        These events are to be handled by the mothership only. It may be that the mothership finds events
        that require functions in gui_core to be called, but first and foremost all events should be propagated
        upwards to the mothership.
        """

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
        """
        Helper function for SubGUI's to get the current mode of the PlanetView without needing
        direct access to the class.
        """

        return self.planet_view.mode

    def is_planet_view_start_pos_locked(self) -> bool:
        """
        Helper function for SubGUI's to check if the starting position inputs of the planet view SubGUI is
        currently locked without needing direct access to the class.
        """

        return self.sub_GUIs.get("planet_view").start_pos_locked

    def get_planet_view_start_pos(self) -> Optional[tuple[str, Direction]]:
        """
        Helper function for SubGUI's to to get the values from the starting position inputs of the
        planet view SubGUI without needing direct access to the class.

        Can return None if the starting position is not locked.
        """

        planet_view_gui = self.sub_GUIs.get("planet_view")
        return planet_view_gui.start_node_id, planet_view_gui.start_direction

    def can_switch_to_edit_mode(self) -> bool:
        """
        Returns whether the GUI is in a state that allows for switching the planet view to edit mode.
        """

        return self.sub_GUIs.get("coms").tank_header_state == ComsSubGUI.TankHeaderState.ADDING_TANK

    def display_tank_internal_planet(self, event: TankPlanetUpdate):
        """
        Helper function for updating the TankMapSubGUI and rendering a new image based on the given TankPlanetUpdate
        without needing access to the TankMapSubGUI class.
        """

        self.sub_GUIs.get("tank_map").update_image(
            TankMapRenderer.render_map_image(event.planet, event.cur_node, event.target_node,
                                             event.target_route, event.depart_dir)
        )

    def remove_tank(self):
        """
        Removes the currently connected tank client from all SubGUIs.
        """

        self.sub_GUIs.get("tank_map").remove_image()
        self.sub_GUIs.get("coms").tank_header_state = ComsSubGUI.TankHeaderState.ADDING_TANK
        self.tank_connection_event()

    def tank_connection_event(self):
        """
        Function to be called whenever an event relating to the connection to the tank client occurs.
        Updates the necessary SubGUIs.
        """

        self.sub_GUIs.get("planet_view").event_update()
        self.sub_GUIs.get("coms").handle_tank_connection_event()

    def handle_planet_view_update(self):
        """
        Function to be called whenever a planet view update necessitates updating the SubGUIs.
        """

        self.sub_GUIs.get("planet_view").event_update()

