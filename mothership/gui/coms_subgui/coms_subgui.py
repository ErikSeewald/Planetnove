from __future__ import annotations
from enum import Enum
import dearpygui.dearpygui as dpg
from mothership.gui import theme
from mothership.gui.planet_view.planet_view import PlanetView
from mothership.gui.sub_gui import SubGUI
from mothership.update_event import AddedTank, UpdateEvent, DisconnectedTank
from mothership.io.communications import Communications


class ComsSubGUI(SubGUI):
    """
    SubGUI responsible for managing the mothership's communications.
    """

    # State
    class TankHeaderState(Enum):
        """
        State of the sub-SubGUI under the header 'tank'
        """

        ADDING_TANK = 0
        CONNECTING = 1
        PENDING_START_MESSAGE = 2
        STARTED = 3
    tank_header_state: TankHeaderState

    # Whether the last attempt to connect failed -> used for changing connect button label
    failed_to_connect_tank: bool

    # Events
    tank_add_event_scheduled: bool
    tank_disconnect_event_scheduled: bool

    # Other modules
    coms: Communications

    def __init__(self, tag: str, gui_core, coms: Communications):
        super().__init__(tag, gui_core)

        self.coms = coms
        self.tank_header_state = self.TankHeaderState.ADDING_TANK
        self.tank_add_event_scheduled = False
        self.tank_disconnect_event_scheduled = False
        self.failed_to_connect_tank = False

        # WINDOW
        with dpg.window(label="Communications", width=400, height=200, no_close=True, tag=self.tag, no_move=True,
                        pos=[10, 250]) as window_id:
            theme.apply_window_theme(window_id)

            # TANK HEADER
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
                                           callback=self._tank_start_message_callback, show=False)
                theme.apply_button_theme(button_id)

    def update(self) -> list[UpdateEvent]:
        events: list[UpdateEvent] = list()

        if self.tank_header_state == self.TankHeaderState.ADDING_TANK:
            self._update_adding_tank_denied_widgets()

        if self.tank_add_event_scheduled:
            self.tank_add_event_scheduled = False
            start_pos = self._gui_core.get_planet_view_start_pos()
            events.append(AddedTank(tank_ip=self.coms.tank_address,
                                    starting_node_id=start_pos[0], arrival_from=start_pos[1]))

        if self.tank_disconnect_event_scheduled:
            self.tank_disconnect_event_scheduled = False
            events.append(DisconnectedTank(tank_ip=self.coms.tank_address))
            self._set_tank_header_state(self.TankHeaderState.ADDING_TANK)
            self._update_all_tank_header_widgets()

        return events

    def switch_to_mode_started(self):
        """
        Switches to 'STARTED' mode and updates the corresponding dpg values.
        """

        self._set_tank_header_state(self.TankHeaderState.STARTED)
        self._update_all_tank_header_widgets()

    def handle_tank_connection_event(self):
        """
        Handles any events relating to an update in the connection to the tank client.
        """

        self._update_all_tank_header_widgets()

    def _set_tank_header_state(self, new_state: TankHeaderState):
        """
        Sets the tank header state to the given new state. Never update it outside of this method.
        """

        self.tank_header_state = new_state

    def _update_all_tank_header_widgets(self):
        """
        Updates all widgets of the tank header based on the current TankHeaderState.
        """

        # TANK ADDED
        tank_added = (self.tank_header_state != self.TankHeaderState.ADDING_TANK and
                      self.tank_header_state != self.TankHeaderState.CONNECTING)

        add_tank_label = "Add tank" if not self.failed_to_connect_tank else "Failed to connect. Try again?"
        dpg.configure_item("add_tank_button", label=add_tank_label, show=not tank_added, enabled=not tank_added)

        dpg.configure_item("tank_ip_input", show=not tank_added, enabled=not tank_added)
        dpg.configure_item("tank_ip_text", default_value=f"Ip address: {dpg.get_value('tank_ip_input')}",
                           show=tank_added)

        self._update_adding_tank_denied_widgets()

        # PENDING MESSAGE
        pending_message = self.tank_header_state == self.TankHeaderState.PENDING_START_MESSAGE
        dpg.configure_item("disconnect_tank_button", show=pending_message)
        dpg.configure_item("start_message_button", show=pending_message)

    def _update_adding_tank_denied_widgets(self):
        """
        Updates all widgets related to denying the option to add a tank client based on the GUI state.
        This is a separate function from _update_all_tank_header_widgets() so that computation time can be saved
        when this function needs to be run for every update during the ADDING_TANK phase.
        """

        adding_tank = self.tank_header_state == self.TankHeaderState.ADDING_TANK

        in_edit_mode = self._gui_core.get_planet_view_mode() == PlanetView.Mode.EDIT
        dpg.configure_item("edit_mode_error", show=in_edit_mode and adding_tank)

        start_pos_locked = self._gui_core.is_planet_view_start_pos_locked()
        dpg.configure_item("no_start_pos_error", show=not start_pos_locked and adding_tank)

        ready_to_add = adding_tank and start_pos_locked and not in_edit_mode
        dpg.configure_item("add_tank_button", show=adding_tank, enabled=ready_to_add)

    def _add_tank_callback(self):
        """
        Callback function for the 'Add Tank' button. Updates the state in two phases:
        1) During the connection -> All other inputs are disabled
        2) After the connection attempt -> Updates widgets based on whether the connection succeeded
        """

        # PHASE 1: Connecting
        self._set_tank_header_state(self.TankHeaderState.CONNECTING)
        self._gui_core.tank_connection_event()

        dpg.configure_item("add_tank_button", show=True, enabled=False, label="Connecting...")
        dpg.configure_item("tank_ip_input", enabled=False)

        connect_result = self.coms.try_connect_tank(dpg.get_value("tank_ip_input"))

        # PHASE 2: After the connection attempt
        self.failed_to_connect_tank = not connect_result
        if not self.failed_to_connect_tank:
            self._set_tank_header_state(self.TankHeaderState.PENDING_START_MESSAGE)
            self.tank_add_event_scheduled = True
        else:
            self._set_tank_header_state(self.TankHeaderState.ADDING_TANK)

        self._gui_core.tank_connection_event()

    def _disconnect_tank_callback(self):
        """
        Callback function for the 'Add Tank' button. Schedules a disconnect event for the next update iteration.
        """

        self.tank_disconnect_event_scheduled = True

    def _tank_start_message_callback(self):
        """
        Callback function for the 'Send start message' button.
        Switches the mode 'STARTED' and calls the send_tank_start_message() of the Communications class.
        """

        self.coms.send_tank_start_message()
        self.switch_to_mode_started()

