import json
from typing import Optional
from mothership.planet_state.tank_entity import TankEntity
from mothership.io.requests import RequestResponse
from planets.code.planet import Planet


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
        taken_path_id = last_node.paths.get(self.tank.departure_direction)
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

        self.arrival_message()

    def arrival_message(self):
        node = self.planet.nodes.get(self.tank.cur_node_id)
        message = {
            "facing_direction": self.tank.facing_direction.name,
            "node_id": node.name,
            "node_coord": {"x": node.coord.x, "y": node.coord.y},
            "available_paths": [direction.name for direction in node.get_available_paths().keys()]
        }
        json_message = json.dumps(message, indent=4)
        print(json_message)

    def on_tank_depart_request(self) -> RequestResponse:
        return RequestResponse.approve(f"Here you go {self.tank.tank_id}")


