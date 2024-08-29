from typing import Optional

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
    sub_GUIs: list[SubGUI]

    # COMS
    coms: Communications

    def __init__(self, draggable_tiles: list[DraggableTile], tile_data: list[Tile], coms: Communications):
        # PLANET VIEW
        self.planet_view = PlanetView(draggable_tiles, tile_data)

        # COMS
        self.coms = coms

        # DEARPYGUI
        dpg.create_context()

        self.sub_GUIs = [
            PlanetViewSubGUI("planet_view", gui_core=self, planet_view=self.planet_view),
            ComsSubGUI("coms", gui_core=self, coms=self.coms)
        ]


        dpg.create_viewport(title='Mothership', width=1400, height=850)
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
        for gui in self.sub_GUIs:
            events.extend(gui.update())

        return events

    def get_planet_view_mode(self) -> PlanetView.Mode:
        return self.planet_view.mode

    def is_start_pos_locked(self) -> bool:
        for gui in self.sub_GUIs:
            if isinstance(gui, PlanetViewSubGUI):
                return gui.start_pos_locked
        return False

    def get_start_pos(self) -> Optional[tuple[str, Direction]]:
        for gui in self.sub_GUIs:
            if isinstance(gui, PlanetViewSubGUI):
                return gui.start_node_id, gui.start_direction
        return None

    def tank_start_message_callback(self):
        self.coms.send_tank_start_message()

