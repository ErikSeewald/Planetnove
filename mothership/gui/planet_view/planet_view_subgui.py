from __future__ import annotations
import dearpygui.dearpygui as dpg
from mothership.gui import theme
from mothership.gui.planet_view.planet_view import PlanetView
from mothership.gui.sub_gui import SubGUI


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

            dpg.add_spacer(height=5)

            # EDIT MODE
            with dpg.collapsing_header(label="Edit mode", default_open=True, tag="edit_mode_header",
                                       show=True) as header_id:
                theme.apply_header_theme(header_id)

                button_id = dpg.add_button(label="Finish (Disabled - tiles must form a single planet)",
                                           callback=self._finish_planet_callback, tag="finish_button", enabled=False)
                theme.apply_button_theme(button_id)

        self.update()

    def update(self):
        if self.planet_view.sub_gui_outdated:
            self._event_update()

    def _event_update(self):
        self._update_finish_button()
        self.planet_view.register_sub_gui_update()

    def _update_finish_button(self):
        if self.planet_view.can_finish_planet():
            dpg.configure_item("finish_button", enabled=True, show=True, label="Finish")
        else:
            dpg.configure_item("finish_button", enabled=False, show=True,
                               label="Finish (Disabled - tiles must form a single planet)")

    def _viewer_mode_switch(self):
        dpg.configure_item("planet_mode_header", show=self.planet_view.mode == PlanetView.Mode.PLANET)
        dpg.configure_item("edit_mode_header", show=self.planet_view.mode == PlanetView.Mode.EDIT)

    def _finish_planet_callback(self):
        self.planet_view.finish_planet()
        self._viewer_mode_switch()