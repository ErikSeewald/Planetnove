from mothership.io.communications import Communications
from mothership.planet_state.planet_state_manager import PlanetStateManager
from mothership.planet_state.tank_entity import TankEntity
from planets.code.planet import Planet


class Mothership:
    """
    Core class representing the mothership.
    """

    planet_manager: PlanetStateManager
    communications: Communications

    def __init__(self):
        self.planet_manager = PlanetStateManager()

    def set_planet(self, planet: Planet):
        self.planet_manager.set_planet(planet)

        # TODO: Remove this debug stuff
        tank = TankEntity("tank")
        tank.cur_node_id = "draven"
        self.planet_manager.set_tank_entity(tank)
