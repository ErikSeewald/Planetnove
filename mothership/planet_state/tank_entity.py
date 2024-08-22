from typing import Optional

from util.direction import Direction


class TankEntity:
    """
    Class representing a tank entity on the mother ship's internal representation of the planet.
    """

    tank_id: str

    cur_node_id: Optional[str]
    last_node_id: Optional[str]
    facing_direction: Direction
    departure_direction: Direction

    def __init__(self, tank_id: str):
        self.tank_id = tank_id
