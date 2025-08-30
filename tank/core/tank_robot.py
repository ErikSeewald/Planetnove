import sys
from enum import Enum

from tank.core.explorer import Explorer
from tank.core.tank_client import TankClient
from tank.movement.line_following import LineFollower
from tank.movement.calibrated_motor import CalibratedMotor
from tank.movement.movement_routines import MovementRoutines
from tank.sensors.infrared import InfraredSensor
from tank.sensors.ultrasonic import Ultrasonic
from tank.signals.LEDs import LEDs
from util.direction import Direction, RelativeDirection
from util.logger import Logger


class TankRobot:
    """
    Core class representing the tank robot. Holds all component and control classes and manages the main
    loop.
    """

    # STATE
    class TankState(Enum):
        INITIALIZING = 0
        LINE_FOLLOWING = 1
        AT_NODE = 2
        READY_TO_DEPART = 3
        FINISHED = 4

    state: TankState

    # COMPONENT CLASSES
    motor: CalibratedMotor
    infrared: InfraredSensor
    ultrasonic: Ultrasonic
    leds: LEDs

    # CONTROL CLASSES
    movement_routines: MovementRoutines
    line_follower: LineFollower
    explorer: Explorer
    client: TankClient
    logger: Logger

    def __init__(self, client: TankClient, leds: LEDs, logger: Logger):
        self.logger = logger
        self.client = client
        self.leds = leds

        # STATE
        self.switch_state(self.TankState.INITIALIZING)

        # COMPONENT CLASSES
        self.motor = CalibratedMotor()
        self.infrared = InfraredSensor()
        self.ultrasonic = Ultrasonic()

        # CONTROL CLASSES
        self.movement_routines = MovementRoutines(self.motor, self.infrared)
        self.line_follower = LineFollower(self.infrared, self.ultrasonic, self.motor,
                                          self.movement_routines, self.leds, self.logger)
        self.explorer = Explorer(logger)

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
            if self.state == self.TankState.FINISHED:
                self.logger.log("Finished!")
                self.leds.rainbow_cycle()
                return

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
        A single 'step' of the line following protocol. Runs until the tank:
        A) has arrived at a new node
        B) has returned to the starting node after encountering an obstacle
        C) has timed out
        """

        follow_result = self.line_follower.follow_to_next_node()

        if follow_result == LineFollower.FollowResult.ARRIVED_AT_NODE:
            self.switch_state(self.TankState.AT_NODE)

        elif follow_result == LineFollower.FollowResult.PATH_BLOCKED:
            self.switch_state(self.TankState.AT_NODE)
            self.explorer.returned_from_path_blocked = True

            # Do not proceed to node arrival until mothership has acknowledged the blocked path
            response = None
            while response is None:
                self.client.send_path_blocked()
                self.logger.log("Waiting for path_blocked_response...")
                response = self.client.get_path_blocked_response()

        elif follow_result == LineFollower.FollowResult.TIMED_OUT:
            self.logger.log("Error: Line following step timed out")
            sys.exit(1)

    def on_node_arrival(self):
        """
        Implements the node arrival protocol. Communicates the arrival to the mothership,
        adjusts the explored planet based on the response and chooses the next move.
        By the end of the function, the tank should be ready to depart.
        """

        response = None
        while response is None:
            self.client.send_node_arrival()
            self.logger.log("Waiting for arrival_response...")
            response = self.client.get_node_arrival_response()

        self.explorer.handle_arrival_response(response)
        self.choose_path()

    def choose_path(self):
        """
        Chooses a new path based on the current state and objective. Then communicates that choice
        to the mothership and handles the response. If the choice is approved, the tank's state becomes
        READY_TO_DEPART. If it is denied, the function chooses a different path.
        Communicates to the mothership accordingly if all chosen paths are denied or the planet is fully explored.
        """

        depart_dir = Direction.UNKNOWN
        rejected_directions: set[Direction] = set()

        choice_rejected = True
        while choice_rejected:
            depart_dir = self.explorer.choose_path(rejected_directions)
            if depart_dir == Direction.UNKNOWN:
                self.handle_no_path_found()
                return

            response = None
            while response is None:
                self.client.send_path_chosen(depart_dir)
                self.logger.log("Waiting for path_chosen_response...")
                response = self.client.get_path_chosen_response()

            if response['request_response']['is_approved']:
                self.explorer.next_departure_direction = depart_dir
                self.logger.log(f"Next departure direction: {self.explorer.next_departure_direction}")
                choice_rejected = False
            else:
                rejected_directions.add(depart_dir)

        self.client.send_internal_planet_update(self.explorer.planet, self.explorer.cur_node_id,
                                                self.explorer.target_node_id, self.explorer.target_route, depart_dir)
        self.leds.global_direction_indicator(self.explorer.facing_direction)
        self.switch_state(self.TankState.READY_TO_DEPART)

    def handle_no_path_found(self):
        """
        Handles the case of the path choosing function failing to choose a new path.
        The mothership is alerted of the tank either having finished or being stuck, a final planet update is sent
        and the TankState is switched to FINISHED.
        """
        if self.explorer.finished_exploring():
            self.client.send_finished_exploring()
        else:
            self.client.send_stuck()

        # Send internal planet afterward. Due to it being such a large
        # message, if the smaller finish message is sent after this one it could mix into
        # the chunks of internal planet message that are currently being processed
        # by the mothership and cause an unparsable message.
        self.client.send_internal_planet_update(self.explorer.planet, self.explorer.cur_node_id,
                                                self.explorer.target_node_id, self.explorer.target_route,
                                                Direction.UNKNOWN)
        self.state = self.TankState.FINISHED

    def depart_from_node(self):
        """
        Handles node departure. Calls the departure movement routine with the correct relative direction to the
        facing direction and updates corresponding state variables.
        """

        target_direction = RelativeDirection.from_absolute(self.explorer.facing_direction,
                                                           self.explorer.next_departure_direction)
        self.logger.log(f"Next relative target direction: {target_direction}")

        self.leds.turn_animation(target_direction)
        self.movement_routines.node_departure(target_direction)

        self.leds.node_departure(
            LEDs.DepartureType.NEW_PATH if not self.explorer.target_route \
                else LEDs.DepartureType.TARGET_NEXT if len(self.explorer.target_route.path_id_list) == 1 \
                else LEDs.DepartureType.KNOWN_PATH
        )

        self.explorer.node_departure()
        self.switch_state(self.TankState.LINE_FOLLOWING)

    def stop_all(self):
        """
        Stops all components (e.g. the motors) from running.
        """

        self.logger.log("Stopping all motors")
        self.motor.stop_motors()

        self.logger.log("Turning off LEDs")
        self.leds.reset_all()
