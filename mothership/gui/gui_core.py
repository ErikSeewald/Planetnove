from mothership.gui.update_event import UpdateEvent
from mothership.gui.planet_view.planet_view import PlanetView
from mothership.gui.planet_view.planet_view_subgui import PlanetViewSubGUI
from mothership.gui.planet_view.tile import DraggableTile
from mothership.gui.coms_subgui.coms_subgui import ComsSubGUI
from mothership.gui.sub_gui import SubGUI
from mothership.io.communications import Communications
from planets.code.tile_data import Tile
import dearpygui.dearpygui as dpg


class GUICore:
    """
    Core class handling the GUI loop of the mothership.
    """

    # PLANET VIEW
    planet_view: PlanetView

    # DEARPYGUI
    sub_GUIs: list[SubGUI]

    def __init__(self, draggable_tiles: list[DraggableTile], tile_data: list[Tile], coms: Communications):
        # PLANET VIEW
        self.planet_view = PlanetView(draggable_tiles, tile_data)

        # DEARPYGUI
        dpg.create_context()

        self.sub_GUIs = [
            PlanetViewSubGUI("planet_view", gui_core=self, planet_view=self.planet_view),
            ComsSubGUI("coms", gui_core=self, coms=coms)
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
            gui.update()

        return events
