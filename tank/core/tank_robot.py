import time
from enum import Enum

from pygame import Vector2

from planets.code.path import Path
from planets.code.planet import Planet
from tank.core.tank_client import TankClient
from tank.movement.line_following import LineFollower
from tank.movement.calibrated_motor import CalibratedMotor
from tank.movement.movement_routines import MovementRoutines
from tank.sensors.infrared import InfraredSensor
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
        ERROR = -1
    state: TankState

    facing_direction: Direction
    last_departure_direction: Direction
    next_departure_direction: Direction

    # EXPLORED PLANET
    planet: Planet
    cur_node_id: str
    cur_node_coord: Vector2

    # COMPONENT CLASSES
    motor: CalibratedMotor
    infrared: InfraredSensor

    # CONTROL CLASSES
    movement_routines: MovementRoutines
    line_follower: LineFollower
    client: TankClient
    logger: Logger

    def __init__(self, client: TankClient, logger: Logger):
        self.logger = logger

        self.client = client
        if not client.connected_to_server:
            raise ValueError("Failed to initialize TankRobot: TankClient is not connected to the server.")

        self.switch_state(self.TankState.INITIALIZING)

        self.facing_direction = Direction.UNKNOWN
        self.last_departure_direction = Direction.UNKNOWN
        self.next_departure_direction = Direction.UNKNOWN

        self.planet = Planet(nodes=dict(), known_paths=dict())
        self.cur_node_id = "None"
        self.cur_node_coord = Vector2(-1, -1)

        self.motor = CalibratedMotor()
        self.infrared = InfraredSensor()

        self.movement_routines = MovementRoutines(self.motor)
        self.line_follower = LineFollower(self.infrared, self.motor, self.movement_routines)

    def switch_state(self, new_state: TankState):
        """
        Switches the TankState and handles logging.
        Never change the state outside of this function.
        """

        self.state = new_state
        self.logger.log(f"New state: {new_state}")

    def core_loop(self):
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

            if self.state == self.TankState.ERROR:
                self.logger.log("!!! ERROR STATE !!!")
                time.sleep(1) # TODO: Handle error

    def line_follow_step(self):
        follow_result = self.line_follower.follow_to_next_node()

        if follow_result == LineFollower.FollowResult.ARRIVED_AT_NODE:
            self.switch_state(self.TankState.AT_NODE)

        elif follow_result == LineFollower.FollowResult.TIMED_OUT:
            self.logger.log("Error: Line following step timed out")
            self.switch_state(self.TankState.ERROR)

    def on_node_arrival(self):
        self.client.send_node_arrival()

        # RESPONSE
        response = None
        while response is None:
            self.logger.log("Waiting for arrival_response...")
            response = self.client.get_node_arrival_response()

        self.facing_direction = Direction.from_str(response['facing_direction'])
        self.logger.log(f"Facing {self.facing_direction}")

        prev_node_id = self.cur_node_id
        self.cur_node_id = response['node_id']
        self.logger.log(f"At node {self.cur_node_id}")

        node_coord = response['node_coord']
        self.cur_node_coord = Vector2(int(node_coord['x']), int(node_coord['y']))
        self.logger.log(f"With node coord {self.cur_node_coord}")

        path_dirs = [Direction.from_str(d) for d in response['available_paths']]
        self.logger.log(f"Available paths: {path_dirs}")

        # ADD NEW NODE TO EXPLORED PLANET
        self.planet.add_node_with_unknown_paths(self.cur_node_id, self.cur_node_coord, set(path_dirs))

        # ADD TAKEN PATH TO EXPLORED PLANET
        arrival_path_dir = self.facing_direction.invert()
        arrival_path_id = f"{prev_node_id}-{self.cur_node_id}"
        node_a_with_dir = f"{prev_node_id}:{self.last_departure_direction.abbreviation()}"
        node_b_with_dir = f"{self.cur_node_id}:{arrival_path_dir.abbreviation()}"
        arrival_path = Path(arrival_path_id, node_a_with_dir, node_b_with_dir)
        self.planet.add_path(arrival_path)
        self.logger.log(f"Added path {arrival_path} to the planet map")
        self.planet.nodes.get(self.cur_node_id).set_path(arrival_path_dir, arrival_path.name)

        self.choose_path()

    def choose_path(self, rejected_directions: set[Direction] = None):
        # TODO: Replace with actual path choosing and handle rejected_directions
        depart_dir = Direction.from_str(input("In which direction (N,E,S,W) should I depart? "))
        self.client.send_path_chosen(depart_dir)

        # RESPONSE
        response = None
        while response is None:
            self.logger.log("Waiting for path_chosen_response...")
            response = self.client.get_path_chosen_response()

        if response['is_approved']:
            self.next_departure_direction = depart_dir
            self.logger.log(f"Next departure direction: {self.next_departure_direction}")
            self.switch_state(self.TankState.READY_TO_DEPART)
        else:
            if rejected_directions is None:
                rejected_directions = set()
            self.choose_path(rejected_directions=rejected_directions.add(depart_dir))

    def depart_from_node(self):
        """
        Handles node departure. Calls the departure movement routine with the correct relative direction to the
        facing direction and updates corresponding line following strategy and state variables.
        """

        # RELATIVE TARGET DIRECTION
        target_direction = RelativeDirection.from_absolute(self.facing_direction, self.next_departure_direction)
        if target_direction == RelativeDirection.UNKNOWN:
            raise ValueError(f"Calculated invalid {target_direction=} from {self.facing_direction=} and "
                             f"{self.next_departure_direction=}")

        self.movement_routines.node_departure(target_direction)

        # LINE FOLLOWING STRATEGY
        if target_direction == RelativeDirection.RIGHT:
            self.line_follower.switch_strategy(LineFollower.StrategyState.ROTATE_RIGHT)
        elif target_direction == RelativeDirection.LEFT:
            self.line_follower.switch_strategy(LineFollower.StrategyState.ROTATE_LEFT)

        # STATE VARIABLES
        self.last_departure_direction = self.next_departure_direction
        self.next_departure_direction = Direction.UNKNOWN

        self.switch_state(self.TankState.LINE_FOLLOWING)
