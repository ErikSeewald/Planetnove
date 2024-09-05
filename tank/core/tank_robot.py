import sys
import time
from enum import Enum
from typing import Optional

from pygame import Vector2

from planets.code.path import Path
from planets.code.planet import Planet
from planets.code.route import Route
from tank.core.tank_client import TankClient
#DEBUG from tank.movement.line_following import LineFollower
#DEBUG from tank.movement.calibrated_motor import CalibratedMotor
#DEBUG from tank.movement.movement_routines import MovementRoutines
#DEBUG from tank.sensors.infrared import InfraredSensor
from util.direction import Direction, RelativeDirection
from util.logger import Logger


class TankRobot:
    """
    Core class representing the tank robot. Holds all component and control classes and manages the main
    loop.
    """

    # STATE VARIABLES
    class TankState(Enum):
        INITIALIZING = 0
        LINE_FOLLOWING = 1
        AT_NODE = 2
        READY_TO_DEPART = 3
    state: TankState

    facing_direction: Direction
    last_departure_direction: Direction
    next_departure_direction: Direction

    # EXPLORED PLANET
    planet: Planet
    cur_node_id: str
    cur_node_coord: Vector2
    reached_first_node: bool
    target_node_id: Optional[str] # None if there is currently no target
    target_route: Optional[Route]

    # COMPONENT CLASSES
    #DEBUG motor: CalibratedMotor
    #DEBUG infrared: InfraredSensor

    # CONTROL CLASSES
    #DEBUG movement_routines: MovementRoutines
    #DEBUG line_follower: LineFollower
    client: TankClient
    logger: Logger

    def __init__(self, client: TankClient, logger: Logger):
        self.logger = logger
        self.client = client

        # STATE VARIABLES
        self.switch_state(self.TankState.INITIALIZING)

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

        # CONTROL CLASSES
        #DEBUG self.motor = CalibratedMotor()
        #DEBUG self.infrared = InfraredSensor()

        #DEBUG self.movement_routines = MovementRoutines(self.motor)
        #DEBUG self.line_follower = LineFollower(self.infrared, self.motor, self.movement_routines)

    def switch_state(self, new_state: TankState):
        """
        Switches the TankState and handles logging.
        Never change the state outside of this function.
        """

        self.state = new_state
        self.logger.log(f"New state: {new_state}")

    def core_loop(self):
        """
        The core loop of the tank's planet exploration. Handles state updates, calls to subroutines and
        communications.
        """

        self.switch_state(self.TankState.LINE_FOLLOWING)

        while True:
            if self.state == self.TankState.LINE_FOLLOWING:
                self.logger.log("Starting line following step")
                self.line_follow_step()

            if self.state == self.TankState.AT_NODE:
                self.logger.log("Arrived at node")
                self.on_node_arrival()

            if self.state == self.TankState.READY_TO_DEPART:
                self.logger.log("Starting departure")
                self.depart_from_node()

    def line_follow_step(self):
        """
        A single 'step' of the line following protocol. Runs until the tank has arrived at a new node
        and updates state variables accordingly.
        """

        """ DEBUG
        follow_result = self.line_follower.follow_to_next_node()

        if follow_result == LineFollower.FollowResult.ARRIVED_AT_NODE:
            self.switch_state(self.TankState.AT_NODE)

        elif follow_result == LineFollower.FollowResult.TIMED_OUT:
            self.logger.log("Error: Line following step timed out")
            self.switch_state(self.TankState.ERROR)
        """
        self.switch_state(self.TankState.AT_NODE) # DEBUG

    def on_node_arrival(self):
        """
        Implements the node arrival protocol. Communicates the arrival to the mothership,
        adjusts the explored planet based on the response and chooses the next move.
        By the end of the function, the tank should be ready to depart.
        """

        self.client.send_node_arrival()

        # GET RESPONSE
        response = None
        while response is None:
            self.logger.log("Waiting for arrival_response...")
            response = self.client.get_node_arrival_response()

        # HANDLE RESPONSE
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

        self.client.send_internal_planet_update(self.planet, self.cur_node_id)
        self.choose_path(rejected_directions=set())

    def choose_path(self, rejected_directions: set[Direction]):
        """
        Chooses a new path based on the current state and objective. Then communicates that choice
        to the mothership and handles the response. If it the choice approved, the tank's state becomes
        READY_TO_DEPART. If it is denied, the function chooses a different path recursively by updating the
        'rejected_directions' parameter.
        """

        # CHOOSE PATH
        cur_node = self.planet.nodes.get(self.cur_node_id)
        depart_dir = Direction.UNKNOWN

        # Freely exploring or target_route to target_node was blocked
        if self.target_route is None:
            if cur_node.has_unexplored_paths():
                for direction in Direction.real_directions_ordered():
                    if (direction in rejected_directions) or (direction not in cur_node.available_paths):
                        continue
                    if cur_node.direction_to_path_id.get(direction) == "None":
                        depart_dir = direction
                        break

            else:
                # Find closest node with unexplored paths
                shortest_routes = self.planet.shortest_routes_from(self.cur_node_id)
                closest_unexplored = (float("inf"), "None")
                for node_id, route in shortest_routes.items():
                    if route.length < closest_unexplored[0]:
                        if self.planet.nodes.get(node_id).has_unexplored_paths():
                            closest_unexplored = (node_id, closest_unexplored[0])

                if closest_unexplored[1] != "None":
                    self.target_node_id = closest_unexplored[1]
                    self.target_route = shortest_routes.get(self.target_node_id)
                else:
                    sys.exit(1)
                    # TODO: Finished message or stuck message

        # Follow target_route
        else:
            next_path = self.planet.paths.get(self.target_route.path_id_list.pop())
            depart_dir = next_path.direction_a if self.cur_node_id == next_path.node_a else next_path.direction_b

        self.client.send_path_chosen(depart_dir)

        # GET RESPONSE
        response = None
        while response is None:
            self.logger.log("Waiting for path_chosen_response...")
            response = self.client.get_path_chosen_response()

        # HANDLE RESPONSE
        if response['request_response']['is_approved']:
            self.next_departure_direction = depart_dir
            self.logger.log(f"Next departure direction: {self.next_departure_direction}")
            self.switch_state(self.TankState.READY_TO_DEPART)
        else:
            rejected_directions.add(depart_dir)
            self.choose_path(rejected_directions)

    def depart_from_node(self):
        """
        Handles node departure. Calls the departure movement routine with the correct relative direction to the
        facing direction and updates corresponding line following strategy and state variables.
        """

        # RELATIVE TARGET DIRECTION
        target_direction = RelativeDirection.from_absolute(self.facing_direction, self.next_departure_direction)
        self.logger.log(f"Next relative target direction: {target_direction}")

        """ DEBUG
        self.movement_routines.node_departure(target_direction)

        # LINE FOLLOWING STRATEGY
        if target_direction == RelativeDirection.RIGHT:
            self.line_follower.switch_strategy(LineFollower.StrategyState.ROTATE_RIGHT)
        elif target_direction == RelativeDirection.LEFT:
            self.line_follower.switch_strategy(LineFollower.StrategyState.ROTATE_LEFT)
        """

        # STATE VARIABLES
        self.last_departure_direction = self.next_departure_direction
        self.next_departure_direction = Direction.UNKNOWN

        self.switch_state(self.TankState.LINE_FOLLOWING)
