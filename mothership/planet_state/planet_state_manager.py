from typing import Optional
from mothership.planet_state.tank_entity import TankEntity
from util.requests import RequestResponse
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

    def remove_tank_entity(self):
        self.tank = None

    def on_tank_arrival(self):
        """
        Updates the planet state and tank entity upon the tank's arrival at a new node based on the previously
        decided path.
        """

        # Tank entity is already initialized with the necessary variables
        if not self.tank.reached_first_node:
            self.tank.reached_first_node = True
            return

        # Returned from blocked path
        if self.tank.returned_from_path_blocked:
            self.tank.returned_from_path_blocked = False
            self.tank.facing_direction = self.tank.facing_direction.invert()
            return

        # Else:
        last_node = self.planet.nodes.get(self.tank.cur_node_id)
        taken_path_id = last_node.direction_to_path_id.get(self.tank.departure_direction)
        taken_path = self.planet.paths.get(taken_path_id)

        if self.tank.cur_node_id == taken_path.node_a and self.tank.departure_direction == taken_path.direction_a:
            self.tank.cur_node_id = taken_path.node_b
            self.tank.facing_direction = taken_path.direction_b.invert()
        else:
            self.tank.cur_node_id = taken_path.node_a
            self.tank.facing_direction = taken_path.direction_a.invert()

    def tank_arrival_response(self) -> dict:
        """
        Returns the message to be sent to the tank client upon node arrival.
        """

        node = self.planet.nodes.get(self.tank.cur_node_id)
        return {
            "type": "arrival_response",
            "facing_direction": self.tank.facing_direction.name,
            "node_id": node.name,
            "node_coord": {"x": node.coord.x, "y": node.coord.y},
            "available_paths": [direction.name for direction in node.available_paths]
        }

    def tank_path_chosen_response(self, direction: Direction) -> dict:
        """
        Returns the message to the tank approving or denying the tank's chosen departure direction based
        on the planet state.
        """

        response: RequestResponse

        # VALID DIRECTION
        node = self.planet.nodes.get(self.tank.cur_node_id)
        if node.direction_to_path_id.get(direction) != "None":
            self.tank.departure_direction = direction
            response = RequestResponse.approve("")
        else:
            response = RequestResponse.deny(f"Node {self.tank.cur_node_id} has no valid path in direction {direction}")

        # TODO: Remove this DEBUG stuff
        approval = response.is_approved() and input("Approve? Y/N: ").upper() == "Y"
        if approval:
            response = RequestResponse.approve("")
        else:
            response = RequestResponse.deny("User denied you. Sorry :/")

        if response.is_approved():
            self.tank.departure_direction = direction

        return {
            "type": "path_chosen_response",
            "request_response": response.as_dict()
        }

    def handle_tank_path_blocked(self):
        """
        Handles the case where the tank notifies the mothership of the path it has taken being blocked and needing
        to return to the starting node. Updates state variables so that on_tank_arrival() can function normally.
        """

        self.tank.returned_from_path_blocked = True
        self.planet.block_path_in_direction(self.tank.cur_node_id, self.tank.departure_direction)

