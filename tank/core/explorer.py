from typing import Optional
from pygame import Vector2
from planets.code.path import Path
from planets.code.planet import Planet
from planets.code.route import Route
from planets.code.node import Node
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

        if self.cur_node_id == self.target_node_id:
            self.target_node_id = None

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

            id_dir_key_a = Node.id_direction_key(prev_node_id, self.last_departure_direction)
            id_dir_key_b = Node.id_direction_key(self.cur_node_id, arrival_path_dir)

            if not self.planet.path_exists(id_dir_key_a, id_dir_key_b):
                new_path = Path(id_dir_key_a, id_dir_key_b)
                self.planet.add_path(new_path)
                self.planet.remove_blocked_loopback_if_exists(id_dir_key_b)

                # Add path to nodes
                self.planet.nodes.get(self.cur_node_id).set_path(arrival_path_dir, new_path.id)
                self.planet.nodes.get(prev_node_id).set_path(self.last_departure_direction, new_path.id)

                self.logger.log(f"Added path {new_path} to the planet map")

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
        This could be because it is freely exploring the planet or because the route it was following has been
        denied by the mothership or blocked.
        The function either returns an Direction immediately without changing anything else, returns a Direction
        while also beginning to follow a route, or returns Direction.UNKNOWN if no other option was found.
        """

        cur_node = self.planet.nodes.get(self.cur_node_id)

        if cur_node.has_unexplored_paths():
            for direction in Direction.valid_directions_ordered():
                if (direction in rejected_directions) or (direction not in cur_node.available_paths):
                    continue
                if cur_node.direction_to_path_id.get(direction) == "None":
                    return direction

        # Find closest node with unexplored paths
        # (Case: no more unexplored paths or all unexplored paths rejected by mothership)

        # First, temporarily block the paths at the rejected directions so that
        # shortest_routes_from() does not consider them as an option.
        old_lengths: dict[str, float] = dict()
        for direction in rejected_directions:
            path = self.planet.paths.get(cur_node.direction_to_path_id.get(direction))
            if path:
                old_lengths[path.id] = path.length
                path.length = float("inf")

        # Then get shortest routes
        shortest_routes = self.planet.shortest_routes_from(self.cur_node_id)

        # Now unblock and reset the path lengths
        for path_id, length in old_lengths.items():
            self.planet.paths[path_id].length = length

        # Then find the closest unexplored node
        closest_unexplored = (float("inf"), "None")
        for node_id, route in shortest_routes.items():
            if node_id != self.cur_node_id and route.length < closest_unexplored[0]:
                if self.planet.nodes.get(node_id).has_unexplored_paths():
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
        """

        # Remove last taken path from the route. This only happens at the start
        # of the next choose_path iteration so that functions following
        # this one but before arriving at the next route still see it in the list.
        if len(self.target_route.path_id_list) > 0:
            self.target_route.path_id_list.pop()

        if self.cur_node_id == self.target_node_id:
            self.target_node_id = None
            self.target_route = None
            return self.choose_path_no_route(rejected_directions)

        next_path = self.planet.paths.get(self.target_route.path_id_list[-1])  # do not pop it yet
        next_dir = next_path.direction_a if self.cur_node_id == next_path.node_a else next_path.direction_b
        if next_dir in rejected_directions:
            self.target_route = None
            self.target_node_id = None
            return self.choose_path_no_route(rejected_directions)
        else:
            return next_dir

    def node_departure(self):
        """
        Updates state variables for node departure
        """

        self.last_departure_direction = self.next_departure_direction
        self.next_departure_direction = Direction.UNKNOWN

    def finished_exploring(self) -> bool:
        """
        Returns whether exploration is finished. This is the case if the internal
        planet holds no more nodes with unexplored paths.

        (Note that, if the planet has nodes that are unreachable from the node network that the tank is on,
        the planet is still considered fully explored as long as only the mothership knows of these nodes.)
        """

        for node in self.planet.nodes.values():
            if node.has_unexplored_paths():
                return False
        return True
