from typing import Optional

from util.direction import Direction


class TankEntity:
    """
    Class representing a tank entity on the mother ship's internal representation of the planet.
    """

    tank_ip: str

    cur_node_id: str
    last_node_id: Optional[str]
    facing_direction: Direction
    departure_direction: Optional[Direction]

    reached_first_node: bool
    returned_from_path_blocked: bool

    def __init__(self, tank_id: str, cur_node_id: str, facing_direction: Direction):
        self.tank_ip = tank_id
        self.cur_node_id = cur_node_id
        self.facing_direction = facing_direction
        self.reached_first_node = False
        self.returned_from_path_blocked = False

