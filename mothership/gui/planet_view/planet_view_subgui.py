from __future__ import annotations
import dearpygui.dearpygui as dpg
from mothership.gui import theme
from mothership.gui.planet_view.planet_view import PlanetView
from mothership.gui.sub_gui import SubGUI
from mothership.gui.update_event import TileGrabbed, TileReleased


class PlanetViewSubGUI(SubGUI):

    planet_view: PlanetView

    def __init__(self, tag: str, gui_core, planet_view: PlanetView):
        super().__init__(tag, gui_core)
        self.planet_view = planet_view

        # WINDOW
        with dpg.window(label="Planet View", width=400, height=200, no_close=True, tag=self.tag,
                        pos=[10, 250]) as window_id:
            theme.apply_window_theme(window_id)

            # PLANET MODE
            with dpg.collapsing_header(label="Planet mode", default_open=True, tag="planet_mode_header",
                                       show=False) as header_id:
                theme.apply_header_theme(header_id)

                button_id = dpg.add_button(label="Edit planet",
                                           callback=self._edit_callback, tag="edit_button", enabled=False)
                theme.apply_button_theme(button_id)

            # EDIT MODE
            with dpg.collapsing_header(label="Edit mode", default_open=True, tag="edit_mode_header",
                                       show=True) as header_id:
                theme.apply_header_theme(header_id)

                button_id = dpg.add_button(label="Finish (Disabled - tiles must form a single planet)",
                                           callback=self._finish_planet_callback, tag="finish_button", enabled=False)
                theme.apply_button_theme(button_id)

        self.update()

    def update(self):
        if self.event_update_needed():
            self._event_update()

    def event_update_needed(self) -> bool:
        for event in self.planet_view.update_events:
            if isinstance(event, TileGrabbed) or isinstance(event, TileReleased):
                return True
        return False

    def _event_update(self):
        self._update_finish_button()
        self._update_edit_button()

    def _update_finish_button(self):
        if self.planet_view.can_finish_planet():
            dpg.configure_item("finish_button", enabled=True, show=True, label="Finish")
        else:
            dpg.configure_item("finish_button", enabled=False, show=True,
                               label="Finish (Disabled - tiles must form a single planet)")

    def _update_edit_button(self):
        if self.planet_view.can_switch_to_edit_mode():
            dpg.configure_item("edit_button", enabled=True, show=True, label="Edit planet")
        else:
            dpg.configure_item("edit_button", enabled=False, show=True, label="Edit planet (Disabled)")

    def _viewer_mode_switch(self):
        dpg.configure_item("planet_mode_header", show=self.planet_view.mode == PlanetView.Mode.PLANET)
        dpg.configure_item("edit_mode_header", show=self.planet_view.mode == PlanetView.Mode.EDIT)

    def _finish_planet_callback(self):
        self.planet_view.finish_planet()
        self._viewer_mode_switch()

    def _edit_callback(self):
        self.planet_view.switch_mode(PlanetView.Mode.EDIT)
        self._viewer_mode_switch()

