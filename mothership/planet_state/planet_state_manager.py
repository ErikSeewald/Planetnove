import json
from typing import Optional
from mothership.planet_state.tank_entity import TankEntity
from mothership.io.requests import RequestResponse
from planets.code.planet import Planet
from util.direction import Direction


class PlanetStateManager:
    """
    Class managing the mother ship's internal representation of the planet, including the entities on it.
    """

    planet: Optional[Planet]
    tank: Optional[TankEntity]

    def __init__(self):
        pass

    def set_planet(self, planet: Planet):
        self.planet = planet

    def set_tank_entity(self, tank_entity: TankEntity):
        self.tank = tank_entity

    def on_tank_arrival(self):
        last_node = self.planet.nodes.get(self.tank.cur_node_id)
        taken_path_id = last_node.known_paths.get(self.tank.departure_direction)
        taken_path = self.planet.paths.get(taken_path_id)

        if taken_path is None:
            print("Not allowed")
            return

        if self.tank.cur_node_id == taken_path.node_a and self.tank.departure_direction == taken_path.direction_a:
            self.tank.cur_node_id = taken_path.node_b
            self.tank.facing_direction = taken_path.direction_b.invert()
        else:
            self.tank.cur_node_id = taken_path.node_a
            self.tank.facing_direction = taken_path.direction_a.invert()

    def tank_arrival_response(self) -> dict:
        node = self.planet.nodes.get(self.tank.cur_node_id)
        return {
            "type": "arrival_response",
            "facing_direction": self.tank.facing_direction.name,
            "node_id": node.name,
            "node_coord": {"x": node.coord.x, "y": node.coord.y},
            "available_paths": [direction.name for direction in node.available_paths]
        }

    def tank_path_chosen_response(self, direction: Direction) -> dict:
        response: RequestResponse

        # TODO: Replace with commented out code after debugging
        approval = input("Approve? Y/N: ")
        if approval.upper() == "Y":
            response = RequestResponse.approve("")
        else:
            response = RequestResponse.deny("User denied you. Sorry :/")

        """
        # VALID DIRECTION
        if self.planet.node_has_path_direction(self.tank.cur_node_id, direction):
            self.tank.departure_direction = direction
            response = RequestResponse.approve("")
        else:
            response = RequestResponse.deny(f"Node {self.tank.cur_node_id} has no valid path in direction {direction}")
        """

        return {
            "type": "path_chosen_response",
            "request_response": response.as_dict()
        }
