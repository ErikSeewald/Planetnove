from enum import Enum

from tank.movement.PID_controller import PIDController
from tank.movement.movement_routines import MovementRoutines
from tank.sensors.infrared import InfraredSensor, SensorBitmap
from tank.movement.calibrated_motor import CalibratedMotor
from tank.signals.LEDs import LEDs
import time

from tank.sensors.ultrasonic import Ultrasonic
from util.logger import Logger


class LineFollower:
    """
    Class handling the robots line following. Relies on the motor and sensor classes.
    Responsible for line following, node and obstacle detection and rotation adjustments.
    Does not make pathing decisions.
    """

    logger: Logger
    base_speed = 0.8

    # FOLLOW RESULT
    class FollowResult(Enum):
        """
        Enum representing the result of a line following step
        """
        ARRIVED_AT_NODE = 1
        PATH_BLOCKED = 2
        TIMED_OUT = -1

    # STATE
    class State(Enum):
        IDLE = 0
        PID_FOLLOW = 1
        NODE_ARRIVAL = 3

    state: State

    bitmap_to_state: dict[SensorBitmap, State] = {
        SensorBitmap.ALL: State.NODE_ARRIVAL,
    }

    # COMPONENT CLASSES
    infrared: InfraredSensor
    ultrasonic: Ultrasonic
    motor: CalibratedMotor
    leds: LEDs

    # CONTROL CLASSES
    movement_routines: MovementRoutines

    # ATTRIBUTES
    SECONDS_UNTIL_TIMEOUT: float = 600 # Maximum time for a line following step

    def __init__(self, sensor: InfraredSensor, ultrasonic: Ultrasonic,
                 motor: CalibratedMotor, movement_routines: MovementRoutines, leds: LEDs, logger: Logger):
        self.logger = logger
        self.infrared = sensor
        self.ultrasonic = ultrasonic
        self.motor = motor
        self.movement_routines = movement_routines
        self.leds = leds
        self.switch_state(self.State.IDLE)

    def update_state(self, bitmap: SensorBitmap):
        """
        Updates the line following state based on the current state and the given SensorBitmap.
        """

        new_strat = self.bitmap_to_state.get(bitmap)

        if new_strat is not None:
            self.switch_state(new_strat)

    def switch_state(self, new_state: State):
        """
        Switches the line following state and handles logging.
        Never change the state outside of this function.
        """

        self.state = new_state
        self.logger.log(f"New LineFollower state: {new_state}")

    def follow_to_next_node(self) -> FollowResult:
        """
        Main line following loop that runs until the the tank:
        A) has arrived at a new node
        B) has returned to the starting node after encountering an obstacle
        C) has timed out
        """

        self.switch_state(self.State.PID_FOLLOW)
        return self.follow_to_node_with_result(target_result=self.FollowResult.ARRIVED_AT_NODE)

    def follow_to_node_with_result(self, target_result: FollowResult):
        """
        Tries to follow the line to a node and returns the given target_result if a node is reached successfully.
        Returns FollowResult.TIMED_OUT otherwise.
        """

        start_time = time.time()
        while time.time() - start_time < self.SECONDS_UNTIL_TIMEOUT:
            distance = self.ultrasonic.get_distance_cm()
            if distance < 12:
                self.logger.log(f"Encountered obstacle (distance: {distance})")
                return self.handle_obstacle_encounter()

            bitmap = self.infrared.update()
            self.update_state(bitmap)

            if self.state == self.State.NODE_ARRIVAL:
                self.movement_routines.node_arrival()
                self.switch_state(self.State.IDLE)
                return target_result

            if self.state == self.State.PID_FOLLOW:
                self.update_motors_PID(bitmap)

        self.motor.PWM.stop()
        return self.FollowResult.TIMED_OUT

    def update_motors_PID(self, bitmap: SensorBitmap):
        """
        Updates the motors using a PID controller based on the given SensorBitmap.
        """

        # Use new PIDController each time to reset old values
        pid = PIDController(kp=0.75, ki=0.2, kd=0.1)
        correction = pid.compute_correction(bitmap)

        # MOTOR SPEEDS
        left_speed = self.base_speed - correction

        right_speed = self.base_speed + correction

        self.motor.setMotors(left_speed, right_speed)

    def handle_obstacle_encounter(self) -> FollowResult:
        """
        Handles the case of the line follower encountering an obstacle and needing to turn back around to return
        to the starting node.
        """

        self.motor.stop_motors()
        self.leds.obstacle_animation()
        self.movement_routines.turn_around_avoid_obstacle()
        self.switch_state(self.State.PID_FOLLOW)
        return self.follow_to_node_with_result(target_result=self.FollowResult.PATH_BLOCKED)
