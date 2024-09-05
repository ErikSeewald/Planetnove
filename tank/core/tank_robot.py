import sys
from enum import Enum
from typing import Optional
from pygame import Vector2
from planets.code.path import Path
from planets.code.planet import Planet
from planets.code.route import Route
from tank.core.explorer import Explorer
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

    # STATE
    class TankState(Enum):
        INITIALIZING = 0
        LINE_FOLLOWING = 1
        AT_NODE = 2
        READY_TO_DEPART = 3

    state: TankState

    # COMPONENT CLASSES
    #DEBUG motor: CalibratedMotor
    #DEBUG infrared: InfraredSensor

    # CONTROL CLASSES
    #DEBUG movement_routines: MovementRoutines
    #DEBUG line_follower: LineFollower
    explorer: Explorer
    client: TankClient
    logger: Logger

    def __init__(self, client: TankClient, logger: Logger):
        self.logger = logger
        self.client = client

        # STATE
        self.switch_state(self.TankState.INITIALIZING)

        # CONTROL CLASSES
        #DEBUG self.motor = CalibratedMotor()
        #DEBUG self.infrared = InfraredSensor()

        #DEBUG self.movement_routines = MovementRoutines(self.motor)
        #DEBUG self.line_follower = LineFollower(self.infrared, self.motor, self.movement_routines)
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
        self.explorer.handle_arrival_response(response)
        self.choose_path()

    def choose_path(self):
        """
        Chooses a new path based on the current state and objective. Then communicates that choice
        to the mothership and handles the response. If it the choice approved, the tank's state becomes
        READY_TO_DEPART. If it is denied, the function chooses a different path recursively by updating the
        'rejected_directions' parameter.
        """

        # CHOOSE PATH
        choice_rejected = True
        rejected_directions: set[Direction] = set()
        while choice_rejected:
            depart_dir = self.explorer.choose_path(rejected_directions)

            # GET RESPONSE
            response = None
            while response is None:
                self.logger.log("Waiting for path_chosen_response...")
                response = self.client.get_path_chosen_response()

            # HANDLE RESPONSE
            if response['request_response']['is_approved']:
                self.explorer.next_departure_direction = depart_dir
                self.logger.log(f"Next departure direction: {self.explorer.next_departure_direction}")
                self.switch_state(self.TankState.READY_TO_DEPART)
                break
            else:
                rejected_directions.add(depart_dir)

        # INTERNAL PLANET UPDATE
        self.client.send_internal_planet_update(self.explorer.planet, self.explorer.cur_node_id,
                                                self.explorer.target_node_id, self.explorer.target_route, depart_dir)

        if self.explorer.target_route and self.explorer.target_route.path_id_list:
            # Only remove now so that we send it int the planet update
            self.explorer.target_route.path_id_list.pop()

    def depart_from_node(self):
        """
        Handles node departure. Calls the departure movement routine with the correct relative direction to the
        facing direction and updates corresponding line following strategy and state variables.
        """

        # RELATIVE TARGET DIRECTION
        target_direction = RelativeDirection.from_absolute(self.explorer.facing_direction,
                                                           self.explorer.next_departure_direction)
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
        self.explorer.last_departure_direction = self.explorer.next_departure_direction
        self.explorer.next_departure_direction = Direction.UNKNOWN

        self.switch_state(self.TankState.LINE_FOLLOWING)
