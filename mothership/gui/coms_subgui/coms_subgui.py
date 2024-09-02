from __future__ import annotations
from enum import Enum
import dearpygui.dearpygui as dpg
from mothership.gui import theme
from mothership.gui.planet_view.planet_view import PlanetView
from mothership.gui.sub_gui import SubGUI
from mothership.update_event import AddedTank, UpdateEvent, DisconnectedTank
from mothership.io.communications import Communications


class ComsSubGUI(SubGUI):

    class TankHeaderState(Enum):
        ADDING_TANK = 0
        CONNECTING = 1
        PENDING_START_MESSAGE = 2
        STARTED = 3
    tank_header_state: TankHeaderState

    coms: Communications

    tank_add_event_scheduled: bool
    tank_disconnect_event_scheduled: bool

    def __init__(self, tag: str, gui_core, coms: Communications):
        super().__init__(tag, gui_core)

        self.coms = coms
        self.tank_header_state = self.TankHeaderState.ADDING_TANK
        self.tank_add_event_scheduled = False
        self.tank_disconnect_event_scheduled = False

        # WINDOW
        with dpg.window(label="Communications", width=400, height=200, no_close=True, tag=self.tag, no_move=True,
                        pos=[10, 250]) as window_id:
            theme.apply_window_theme(window_id)

            # PLANET MODE
            with dpg.collapsing_header(label="Tank", default_open=True, tag="tank_header") as header_id:
                theme.apply_header_theme(header_id)

                # ADDING TANK
                button_id = dpg.add_button(label="Add tank",
                                           callback=self._add_tank_callback, tag="add_tank_button", enabled=False)
                theme.apply_button_theme(button_id)

                input_id = dpg.add_input_text(hint="IP-Address", tag="tank_ip_input")
                theme.apply_input_theme(input_id)

                text_id = dpg.add_text("Planet view is still in EDIT mode", tag="edit_mode_error", show=False)
                theme.apply_error_msg_theme(text_id)

                text_id = dpg.add_text("Starting position is not set", tag="no_start_pos_error", show=False)
                theme.apply_error_msg_theme(text_id)

                # TANK ADDED
                text_id = dpg.add_text("", tag="tank_ip_text", show=False)
                theme.apply_text_theme(text_id)

                button_id = dpg.add_button(label="Disconnect tank", tag="disconnect_tank_button",
                                           callback=self._disconnect_tank_callback, show=False)
                theme.apply_button_theme(button_id)

                # START MESSAGE
                button_id = dpg.add_button(label="Send start message", tag="start_message_button",
                                           callback=self._gui_core.tank_start_message_callback, show=False)
                theme.apply_button_theme(button_id)

    def update(self) -> list[UpdateEvent]:
        events: list[UpdateEvent] = list()

        if self.tank_header_state == self.TankHeaderState.ADDING_TANK:
            self._update_adding_error_widgets()

        if self.tank_add_event_scheduled:
            self.tank_add_event_scheduled = False
            start_pos = self._gui_core.get_start_pos()
            events.append(AddedTank(tank_ip=self.coms.tank_address,
                                    starting_node_id=start_pos[0], arrival_from=start_pos[1]))

        if self.tank_disconnect_event_scheduled:
            self.tank_disconnect_event_scheduled = False
            events.append(DisconnectedTank(tank_ip=self.coms.tank_address))
            self._disconnecting_tank_update()

        return events

    def _disconnecting_tank_update(self):
        self.tank_header_state = self.TankHeaderState.ADDING_TANK
        self.handle_tank_connection_event()

    def _update_adding_tank_widgets(self):
        tank_added = (self.tank_header_state != self.TankHeaderState.ADDING_TANK and
                      self.tank_header_state != self.TankHeaderState.CONNECTING)

        dpg.configure_item("add_tank_button", label="Add tank", show=not tank_added, enabled=not tank_added)
        dpg.configure_item("tank_ip_input", show=not tank_added, enabled=not tank_added)

        dpg.configure_item("tank_ip_text", default_value=f"Ip address: {dpg.get_value('tank_ip_input')}",
                           show=tank_added)

    def _update_adding_error_widgets(self):
        adding_tank = self.tank_header_state == self.TankHeaderState.ADDING_TANK

        in_edit_mode = self._gui_core.get_planet_view_mode() == PlanetView.Mode.EDIT
        dpg.configure_item("edit_mode_error", show=in_edit_mode and adding_tank)

        start_pos_locked = self._gui_core.is_start_pos_locked()
        dpg.configure_item("no_start_pos_error", show=not start_pos_locked and adding_tank)

        ready_to_add = adding_tank and start_pos_locked and not in_edit_mode
        dpg.configure_item("add_tank_button", show=adding_tank, enabled=ready_to_add)

    def _add_tank_callback(self):
        self.tank_header_state = self.TankHeaderState.CONNECTING
        self._gui_core.tank_connection_event()

        dpg.configure_item("add_tank_button", enabled=False, label="Connecting...")
        dpg.configure_item("tank_ip_input", enabled=False)

        connect_result = self.coms.try_connect_tank(dpg.get_value("tank_ip_input"))
        if connect_result:
            self.tank_header_state = self.TankHeaderState.PENDING_START_MESSAGE
            self._update_adding_tank_widgets()
            dpg.configure_item("start_message_button", show=True)
            dpg.configure_item("disconnect_tank_button", show=True)
            self.tank_add_event_scheduled = True
        else:
            self.tank_header_state = self.TankHeaderState.ADDING_TANK
            dpg.configure_item("add_tank_button", enabled=True, label="Failed to connect. Try again?")
            dpg.configure_item("tank_ip_input", enabled=True)
        self._gui_core.tank_connection_event()

    def _disconnect_tank_callback(self):
        self.tank_disconnect_event_scheduled = True

    def switch_to_mode_started(self):
        self.tank_header_state = self.TankHeaderState.STARTED
        dpg.configure_item("start_message_button", show=False)

    def handle_tank_connection_event(self):
        self._update_adding_tank_widgets()
        pending_message = self.tank_header_state == self.TankHeaderState.PENDING_START_MESSAGE
        dpg.configure_item("disconnect_tank_button", show=pending_message)
        dpg.configure_item("start_message_button", show=pending_message)

