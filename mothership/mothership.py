import pygame
from mothership.gui.gui_core import GUICore
from mothership.gui.planet_view.tile import DraggableTile
from mothership.gui.update_event import UpdateEvent, SwitchedToPlanetMode, AddedTank
from mothership.io.communications import Communications
from mothership.planet_state.planet_state_manager import PlanetStateManager
from mothership.planet_state.tank_entity import TankEntity
from planets.code.planet import Planet
from planets.code.tile_data import Tile
import dearpygui.dearpygui as dpg

from util.direction import Direction
from util.logger import Logger


class Mothership:
    """
    Core class representing the mothership.
    """

    planet_manager: PlanetStateManager
    communications: Communications
    gui: GUICore
    clock: pygame.time.Clock
    logger: Logger

    def __init__(self, draggable_tiles: list[DraggableTile], tile_data: list[Tile]):
        self.logger = Logger()
        self.planet_manager = PlanetStateManager()
        self.communications = Communications(planet_manager=self.planet_manager, logger=self.logger)
        self.gui = GUICore(draggable_tiles, tile_data, coms=self.communications)
        self.clock = pygame.time.Clock()

    def loop(self):
        communication_timer = 0
        communication_interval = 1000  # Update communications every second

        while dpg.is_dearpygui_running():
            # GUI
            gui_events = self.gui.update()
            self.handle_gui_events(gui_events)

            # COMMUNICATIONS
            communication_timer += self.clock.get_time()
            if communication_timer >= communication_interval:
                self.communications.update()
                communication_timer = 0

            self.clock.tick(60)

    def handle_gui_events(self, events: list[UpdateEvent]):
        for event in events:

            if isinstance(event, SwitchedToPlanetMode):
                self.set_planet(event.new_planet)

            if isinstance(event, AddedTank):
                tank_entity = TankEntity(event.tank_ip, event.starting_node_id, event.arrival_from.invert())
                self.planet_manager.set_tank_entity(tank_entity)
    def set_planet(self, planet: Planet):
        self.planet_manager.set_planet(planet)
