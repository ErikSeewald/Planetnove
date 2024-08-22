from mothership.planet_state.planet_state_manager import PlanetStateManager


class Communications:
    """
    Class managing the mother ship's communications with entities like the tank robot.
    """

    planet_manager: PlanetStateManager

    def __init__(self, planet_manager: PlanetStateManager):
        self.planet_manager = planet_manager

    def build_tank_arrival_msg(self) -> str:
        msg = f"{self.planet_manager.tank.cur_node_id}"
        print(msg)
        return msg
