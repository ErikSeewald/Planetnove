import sys
from typing import Optional
from pygame import Vector2
from planets.code.path import Path
from planets.code.planet import Planet
from planets.code.route import Route
from util.direction import Direction
from util.logger import Logger


class Explorer:
    logger: Logger

    # DIRECTIONS
    facing_direction: Direction
    last_departure_direction: Direction
    next_departure_direction: Direction

    # EXPLORED PLANET
    planet: Planet
    cur_node_id: str
    cur_node_coord: Vector2
    reached_first_node: bool
    target_node_id: Optional[str]  # None if there is currently no target
    target_route: Optional[Route]

    def __init__(self, logger: Logger):
        self.logger = logger

        # DIRECTIONS
        self.facing_direction = Direction.UNKNOWN
        self.last_departure_direction = Direction.UNKNOWN
        self.next_departure_direction = Direction.UNKNOWN

        # EXPLORED PLANET
        self.planet = Planet(nodes=dict(), paths=dict())
        self.cur_node_id = "None"
        self.cur_node_coord = Vector2(-1, -1)
        self.reached_first_node = False
        self.target_node_id = None
        self.target_route = None

    def handle_arrival_response(self, response: dict):
        self.facing_direction = Direction.from_str(response['facing_direction'])
        path_dirs = {Direction.from_str(d) for d in response['available_paths']}

        prev_node_id = self.cur_node_id
        self.cur_node_id = response['node_id']
        self.cur_node_coord = Vector2(response['node_coord']['x'], response['node_coord']['y'])

        self.logger.log(f"Facing '{self.facing_direction}' at node '{self.cur_node_id}:{self.cur_node_coord}'")
        self.logger.log(f"Available paths: {path_dirs}")

        # ADD NEW NODE TO EXPLORED PLANET
        if self.planet.nodes.get(self.cur_node_id) is None:
            self.planet.add_node_with_unknown_paths(self.cur_node_id, self.cur_node_coord, path_dirs)

        if not self.reached_first_node:
            self.reached_first_node = True
        else:
            # ADD TAKEN PATH TO EXPLORED PLANET
            arrival_path_dir = self.facing_direction.invert()
            node_a_with_dir = f"{prev_node_id}:{self.last_departure_direction.abbreviation()}"
            node_b_with_dir = f"{self.cur_node_id}:{arrival_path_dir.abbreviation()}"

            if not self.planet.path_exists(node_a_with_dir, node_b_with_dir):
                new_path = Path(f"{node_a_with_dir}-{node_b_with_dir}", node_a_with_dir, node_b_with_dir)
                self.planet.add_path(new_path)
                self.logger.log(f"Added path {new_path} to the planet map")

                # Add path to nodes
                self.planet.nodes.get(self.cur_node_id).set_path(arrival_path_dir, new_path.name)
                self.planet.nodes.get(prev_node_id).set_path(self.last_departure_direction, new_path.name)

    def choose_path(self, rejected_directions: set[Direction]):
        """
        Chooses a new path based on the current state and objective. Then communicates that choice
        to the mothership and handles the response. If it the choice approved, the tank's state becomes
        READY_TO_DEPART. If it is denied, the function chooses a different path recursively by updating the
        'rejected_directions' parameter.
        """

        # Freely exploring or target_route to target_node was blocked
        if self.target_route is None:
            return self.choose_path_no_route(rejected_directions)

        # Follow target_route
        else:
            return self.choose_path_with_route(rejected_directions)

    def choose_path_no_route(self, rejected_directions: set[Direction]) -> Direction:
        cur_node = self.planet.nodes.get(self.cur_node_id)

        if cur_node.has_unexplored_paths():
            for direction in Direction.real_directions_ordered():
                if (direction in rejected_directions) or (direction not in cur_node.available_paths):
                    continue
                if cur_node.direction_to_path_id.get(direction) == "None":
                    return direction

        else:
            # Find closest node with unexplored paths
            shortest_routes = self.planet.shortest_routes_from(self.cur_node_id)
            closest_unexplored = (float("inf"), "None")
            for node_id, route in shortest_routes.items():
                if route.length < closest_unexplored[0]:
                    if self.planet.nodes.get(node_id).has_unexplored_paths():
                        closest_unexplored = (closest_unexplored[0], node_id)

            if closest_unexplored[1] != "None":
                self.target_node_id = closest_unexplored[1]
                self.target_route = shortest_routes.get(self.target_node_id)
                return self.choose_path(rejected_directions)
            else:
                sys.exit(1)
                # TODO: Finished message or stuck message

    def choose_path_with_route(self, rejected_directions):
        if self.cur_node_id == self.target_node_id:
            self.target_node_id = None
            self.target_route = None
            return self.choose_path(rejected_directions)

        else:
            next_path = self.planet.paths.get(self.target_route.path_id_list[-1])  # do not pop it yet
            return next_path.direction_a if self.cur_node_id == next_path.node_a else next_path.direction_b
