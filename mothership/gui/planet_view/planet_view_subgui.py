from __future__ import annotations
import dearpygui.dearpygui as dpg
from mothership.gui import theme
from mothership.gui.planet_view.planet_view import PlanetView
from mothership.gui.sub_gui import SubGUI
from mothership.gui.update_event import TileGrabbed, TileReleased, SwitchedToPlanetMode, UpdateEvent
from util.direction import Direction


class PlanetViewSubGUI(SubGUI):

    planet_view: PlanetView

    # STARTING POSITION
    start_pos_locked: bool
    start_node_id: str
    start_direction: Direction

    def __init__(self, tag: str, gui_core, planet_view: PlanetView):
        super().__init__(tag, gui_core)
        self.planet_view = planet_view

        # STARTING POSITION
        self.start_pos_locked = False
        self.start_node_id = "None"
        self.start_direction = Direction.UNKNOWN

        # WINDOW
        with dpg.window(label="Planet View", width=400, height=200, no_close=True, tag=self.tag,
                        pos=[10, 10]) as window_id:
            theme.apply_window_theme(window_id)

            # PLANET MODE
            with dpg.collapsing_header(label="Planet mode", default_open=True, tag="planet_mode_header",
                                       show=False) as header_id:
                theme.apply_header_theme(header_id)

                button_id = dpg.add_button(label="Edit planet",
                                           callback=self._edit_callback, tag="edit_button", enabled=False)
                theme.apply_button_theme(button_id)

                # STARTING POSITION SUB-HEADER
                with dpg.collapsing_header(label=" Starting position", default_open=True, tag="start_header",
                                           show=True) as header_id_2:
                    theme.apply_header_theme(header_id_2)

                    button_id = dpg.add_button(label="Save",
                                               callback=self._save_start_pos_callback,
                                               tag="start_pos_save_button")
                    theme.apply_button_theme(button_id)

                    button_id = dpg.add_button(label="Edit",
                                               callback=self._edit_start_pos_callback,
                                               tag="start_pos_edit_button", show=False)
                    theme.apply_button_theme(button_id)

                    input_id = dpg.add_input_text(hint="Node name", tag="start_node_input")
                    theme.apply_input_theme(input_id)
                    text_id = dpg.add_text("", tag="start_node_text", show=False)
                    theme.apply_text_theme(text_id)

                    input_id = dpg.add_input_text(hint="Arrival from direction", tag="start_direction_input")
                    theme.apply_input_theme(input_id)
                    text_id = dpg.add_text("", tag="start_direction_text", show=False)
                    theme.apply_text_theme(text_id)

            # EDIT MODE
            with dpg.collapsing_header(label="Edit mode", default_open=True, tag="edit_mode_header",
                                       show=True) as header_id:
                theme.apply_header_theme(header_id)

                button_id = dpg.add_button(label="Finish (Disabled - tiles must form a single planet)",
                                           callback=self._finish_planet_callback, tag="finish_button", enabled=False)
                theme.apply_button_theme(button_id)

        self.update()

    def update(self) -> list[UpdateEvent]:
        if self.event_update_needed():
            self._event_update()

        self._update_edit_button()
        return list()

    def event_update_needed(self) -> bool:
        for event in self.planet_view.update_events:
            if isinstance(event, TileGrabbed) or isinstance(event, TileReleased) \
                    or isinstance(event, SwitchedToPlanetMode):
                return True
        return False

    def _event_update(self):
        self._update_finish_button()
        self._update_edit_button()
        self._viewer_mode_switch()

    def _update_finish_button(self):
        if self.planet_view.can_finish_planet():
            dpg.configure_item("finish_button", enabled=True, show=True, label="Finish")
        else:
            dpg.configure_item("finish_button", enabled=False, show=True,
                               label="Finish (Disabled - tiles must form a single planet)")

    def _update_edit_button(self):
        if self.planet_view.mode == PlanetView.Mode.EDIT:
            return

        if self._gui_core.can_switch_to_edit_mode():
            dpg.configure_item("edit_button", enabled=True, show=True, label="Edit planet")
            dpg.configure_item("start_pos_edit_button", enabled=True, label="Edit")
        else:
            dpg.configure_item("edit_button", enabled=False, show=True,
                               label="Edit planet (Disabled - disconnect tank to enable)")
            dpg.configure_item("start_pos_edit_button", enabled=False, label="Edit (Disabled)")

    def _viewer_mode_switch(self):
        dpg.configure_item("planet_mode_header", show=self.planet_view.mode == PlanetView.Mode.PLANET)
        dpg.configure_item("edit_mode_header", show=self.planet_view.mode == PlanetView.Mode.EDIT)

    def _update_start_pos_widgets(self):
        dpg.configure_item("start_pos_save_button", show=not self.start_pos_locked)
        dpg.configure_item("start_node_input", show=not self.start_pos_locked)
        dpg.configure_item("start_direction_input", show=not self.start_pos_locked)

        dpg.configure_item("start_pos_edit_button", show=self.start_pos_locked)
        dpg.configure_item("start_node_text", default_value=f"Node: {self.start_node_id}", show=self.start_pos_locked)
        dpg.configure_item("start_direction_text", default_value=f"Arrival from direction: {self.start_direction.name}",
                           show=self.start_pos_locked)

    def _finish_planet_callback(self):
        self.planet_view.finish_planet()

    def _edit_callback(self):
        self.planet_view.switch_mode(PlanetView.Mode.EDIT)
        self._event_update()

    def _save_start_pos_callback(self):
        # STARTING NODE
        node_id = dpg.get_value("start_node_input")
        if self.planet_view.planet.nodes.get(node_id) is None:
            dpg.set_value("start_node_input", "Node does not exist. Try again.")
            return
        else:
            self.start_node_id = node_id

        # STARTING DIRECTION
        direction = Direction.from_str(dpg.get_value("start_direction_input"))
        if direction is None or direction == Direction.UNKNOWN:
            dpg.set_value("start_direction_input", "Invalid direction. Try again.")
            return
        else:
            # Allow even if path from that direction does not exist so that the tank can be placed on the board
            # at the start in many different configurations.
            self.start_direction = direction

        self.start_pos_locked = True
        self._update_start_pos_widgets()

    def _edit_start_pos_callback(self):
        self.start_pos_locked = False
        self._update_start_pos_widgets()

