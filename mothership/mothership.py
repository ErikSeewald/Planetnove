import time

from mothership.gui.gui_core import GUICore
from mothership.update_event import UpdateEvent, SwitchedToPlanetMode, AddedTank, DisconnectedTank, \
    TankPlanetUpdate, TankConnectionLost, TileGrabbed, TileReleased, TileActivation
from mothership.io.communications import Communications
from mothership.planet_state.planet_state_manager import PlanetStateManager
from mothership.planet_state.tank_entity import TankEntity
from planets.code.planet import Planet
import dearpygui.dearpygui as dpg
from util.logger import Logger
from pygame.time import Clock

class Mothership:
    """
    Core class representing the mothership.
    Handles the main mothership loop, including GUI and communications as well as all update events.
    """

    planet_manager: PlanetStateManager
    communications: Communications
    gui: GUICore
    logger: Logger
    clock: Clock

    def __init__(self):
        self.logger = Logger()
        self.planet_manager = PlanetStateManager()
        self.communications = Communications(planet_manager=self.planet_manager, logger=self.logger)
        self.gui = GUICore(coms=self.communications)
        self.clock = Clock()

    def loop(self):
        """
        The main mothership loop. Runs at 60hz.
        Updates the GUI and communications submodules.
        Handles all update events that get propagated upwards from these submodules.
        """

        while dpg.is_dearpygui_running():
            gui_events = self.gui.update()
            self.handle_gui_events(gui_events)

            coms_events = self.communications.update()
            self.handle_coms_events(coms_events)

            self.clock.tick(60)
        self.gui.exit()

    def handle_gui_events(self, events: list[UpdateEvent]):
        """
        Handles all update events that occurred while updating the GUI.
        """

        for event in events:
            if isinstance(event, SwitchedToPlanetMode):
                self.set_planet(Planet.from_dict(event.new_planet))
                self.gui.handle_planet_view_update()

            elif isinstance(event, AddedTank):
                tank_entity = TankEntity(event.tank_ip, event.starting_node_id, event.arrival_from.invert())
                self.planet_manager.set_tank_entity(tank_entity)

            elif isinstance(event, DisconnectedTank):
                self.disconnect_tank()

            elif isinstance(event, TileGrabbed) or isinstance(event, TileReleased) or isinstance(event, TileActivation):
                self.gui.handle_planet_view_update()

    def handle_coms_events(self, events: list[UpdateEvent]):
        """
        Handles all update events that occurred while updating the communications.
        """

        for event in events:
            if isinstance(event, TankPlanetUpdate):
                self.gui.display_tank_internal_planet(event)

            elif isinstance(event, TankConnectionLost):
                self.logger.log(f"Connection to tank-{event.tank_ip} lost")
                self.handle_tank_disconnected()

    def disconnect_tank(self):
        """
        Disconnects the currently connected tank client and updates the state of the corresponding submodules.
        """

        self.communications.disconnect_tank()
        self.handle_tank_disconnected()

    def handle_tank_disconnected(self):
        """
        Updates the state of all submodules affected by disconnecting the tank client.
        """

        self.planet_manager.remove_tank_entity()
        self.gui.remove_tank()

    def set_planet(self, planet: Planet):
        """
        Sets the mothership's internal planet variable and updates the corresponding submodules.
        """

        self.planet_manager.set_planet(planet)
