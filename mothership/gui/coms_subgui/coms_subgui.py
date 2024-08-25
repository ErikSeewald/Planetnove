from __future__ import annotations
import dearpygui.dearpygui as dpg
from mothership.gui import theme
from mothership.gui.sub_gui import SubGUI
from mothership.io.communications import Communications


class ComsSubGUI(SubGUI):

    tank_added: bool
    adding_tank: bool

    coms: Communications

    def __init__(self, tag: str, gui_core, coms: Communications):
        super().__init__(tag, gui_core)

        self.coms = coms
        self.tank_added = False
        self.adding_tank = True

        # WINDOW
        with dpg.window(label="Communications", width=400, height=200, no_close=True, tag=self.tag,
                        pos=[10, 250]) as window_id:
            theme.apply_window_theme(window_id)

            # PLANET MODE
            with dpg.collapsing_header(label="Tank", default_open=True, tag="tank_header") as header_id:
                theme.apply_header_theme(header_id)

                # ADDING TANK
                button_id = dpg.add_button(label="Add tank",
                                           callback=self._add_tank_callback, tag="add_tank_button")
                theme.apply_button_theme(button_id)

                input_id = dpg.add_input_text(hint="ip-address", tag="tank_ip_input")
                theme.apply_input_theme(input_id)

        self.update()

    def update(self):
        pass

    def _add_tank_callback(self):
        connect_result = self.coms.try_connect_tank(dpg.get_value("tank_ip_input"))


