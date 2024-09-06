import sys
from typing import Optional
from pygame import Vector2
from planets.code.path import Path
from planets.code.planet import Planet
from planets.code.route import Route
from util.direction import Direction
from util.logger import Logger


class Explorer:
    """
    Class implementing the tank's exploration protocol. Handles the internal planet and facing directions.
    """

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

    # STATE
    returned_from_path_blocked: bool  # Set by tank_robot after handling line follower

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

        # STATE
        self.returned_from_path_blocked = False

    def handle_arrival_response(self, response: dict):
        """
        Handles the given arrival response from the mothership. Updates the internal planet as well as the
        direction state variables.
        """

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
            # IF PATH BLOCKED, REFLECT THAT ON THE EXPLORED PLANET
            if self.returned_from_path_blocked:
                self.returned_from_path_blocked = False
                self.planet.block_path_in_direction(self.cur_node_id, self.last_departure_direction)
                return

            # ELSE: ADD TAKEN PATH TO EXPLORED PLANET
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

    def choose_path(self, rejected_directions: set[Direction]) -> Direction:
        """
        Chooses a new path based on the current state, objective and the given rejected directions.
        If no option is found, Direction.UNKNOWN is returned.
        """

        # Freely exploring or target_route to target_node was blocked
        if self.target_route is None:
            return self.choose_path_no_route(rejected_directions)

        # Follow target_route
        else:
            return self.choose_path_with_route(rejected_directions)

    def choose_path_no_route(self, rejected_directions: set[Direction]) -> Direction:
        """
        Implements the path choosing protocol for when the tank is currently not following a route to a target node.
        This could be because it is freely exploring the planet or because the route it was following has been blocked
        or denied by the mothership.
        The function either returns an immediate Direction without changing anything else, returns a Direction
        while also beginning to follow a route, or returns Direction.UNKNOWN if no more option was found.
        """

        cur_node = self.planet.nodes.get(self.cur_node_id)

        if cur_node.has_unexplored_paths():
            for direction in Direction.real_directions_ordered():
                if (direction in rejected_directions) or (direction not in cur_node.available_paths):
                    continue
                if cur_node.direction_to_path_id.get(direction) == "None":
                    return direction

        # Find closest node with unexplored paths
        # (Case: no more unexplored paths or all unexplored paths rejected by mothership)
        shortest_routes = self.planet.shortest_routes_from(self.cur_node_id)
        closest_unexplored = (float("inf"), "None")
        for node_id, route in shortest_routes.items():
            if node_id != self.cur_node_id and route.length < closest_unexplored[0]:
                if self.planet.nodes.get(node_id).has_unexplored_paths():
                    next_path = self.planet.paths.get(route.path_id_list[-1])  # do not pop it yet
                    next_dir = next_path.direction_a if self.cur_node_id == next_path.node_a else next_path.direction_b
                    if next_dir not in rejected_directions:
                        closest_unexplored = (route.length, node_id)

        if closest_unexplored[1] != "None":
            self.target_node_id = closest_unexplored[1]
            self.target_route = shortest_routes.get(self.target_node_id)
            return self.choose_path_with_route(rejected_directions)

        return Direction.UNKNOWN

    def choose_path_with_route(self, rejected_directions: set[Direction]):
        """
        Implements the path choosing protocol for when the tank is currently following a route to a target node.
        The function either returns the next necessary direction on the route or switches to the no-route protocol
        if a) the target node was reached or b) the route was blocked in some way.
        Note that this function does not yet pop the path to be taken off of the route's path list, as that is the
        responsibility of the tank robot's choose_path() function.
        """

        if self.cur_node_id == self.target_node_id:
            self.target_node_id = None
            self.target_route = None
            return self.choose_path_no_route(rejected_directions)

        else:
            next_path = self.planet.paths.get(self.target_route.path_id_list[-1])  # do not pop it yet
            next_dir = next_path.direction_a if self.cur_node_id == next_path.node_a else next_path.direction_b
            if next_dir in rejected_directions:
                self.target_route = None
                self.target_node_id = None
                return self.choose_path_no_route(rejected_directions)
            else:
                return next_dir

    def finished_exploring(self) -> bool:
        """
        Returns whether exploration is finished. This is the case if the internal planet holds no more nodes
        with unexplored paths. Note that if the tank has been blocked from reaching a previously reached but not
        fully explored node, the path choosing function can return Direction.UNKNOWN without finished_exploring()
        being true. It is also important to remember that, if the planet has nodes that are unreachable from the
        node network that the tank is on, the planet is still considered fully explored as long as
        only the mothership knows of these nodes.
        """

        for node in self.planet.nodes.values():
            if node.has_unexplored_paths():
                return False
        return True
