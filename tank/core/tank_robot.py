import time
from enum import Enum
from tank.movement.line_following import LineFollower
from tank.movement.calibrated_motor import CalibratedMotor
from tank.movement.movement_routines import MovementRoutines
from tank.sensors.infrared import InfraredSensor
from tank.core.direction import Direction, RelativeDirection
from tank.core import direction
from tank.core.logger import Logger


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

    # COMPONENT CLASSES
    motor: CalibratedMotor
    infrared: InfraredSensor

    # CONTROL CLASSES
    movement_routines: MovementRoutines
    line_follower: LineFollower
    logger: Logger

    def __init__(self):
        self.logger = Logger()
        self.switch_state(self.TankState.INITIALIZING)

        self.facing_direction = Direction.UNKNOWN
        self.last_departure_direction = Direction.UNKNOWN
        self.next_departure_direction = Direction.UNKNOWN

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
            self.switch_state(self.TankState.ERROR) # TODO: Handle error

    def on_node_arrival(self):
        # TODO: Replace with actual path choosing
        cur_dir = direction.str_to_direction(input("Which direction (N,E,S,W) am I facing? "))
        depart_dir = direction.str_to_direction(input("In which direction (N,E,S,W) should I depart? "))

        self.facing_direction = cur_dir
        self.next_departure_direction = depart_dir

        self.logger.log(f"Facing {self.facing_direction}")
        self.logger.log(f"Next departure direction: {self.next_departure_direction}")
        self.switch_state(self.TankState.READY_TO_DEPART)

    def depart_from_node(self):
        """
        Handles node departure. Calls the departure movement routine with the correct relative direction to the
        facing direction and updates corresponding line following strategy and state variables.
        """

        # RELATIVE TARGET DIRECTION
        target_direction = direction.get_relative_direction(self.facing_direction, self.next_departure_direction)
        if target_direction == RelativeDirection.UNKNOWN:
            self.switch_state(self.TankState.ERROR)  # TODO: Handle error
            return

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
