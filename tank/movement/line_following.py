from enum import Enum

from tank.movement.p_controller import PController
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
    drift_left_correction = 0.1

    # FOLLOW RESULT
    class FollowResult(Enum):
        """
        Enum representing the result of a line following step
        """
        ARRIVED_AT_NODE = 1
        PATH_BLOCKED = 2

    # STATE
    class State(Enum):
        IDLE = 0
        PI_FOLLOW = 1
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
    p_controller: PController

    def __init__(self, sensor: InfraredSensor, ultrasonic: Ultrasonic,
                 motor: CalibratedMotor, movement_routines: MovementRoutines, leds: LEDs, logger: Logger):
        self.logger = logger
        self.infrared = sensor
        self.ultrasonic = ultrasonic
        self.motor = motor
        self.leds = leds

        self.movement_routines = movement_routines
        self.p_controller = PController(kp=0.8)
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
        Main line following loop that runs until the tank:
        A) has arrived at a new node
        B) has returned to the starting node after encountering an obstacle
        C) has timed out
        """

        self.switch_state(self.State.PI_FOLLOW)
        return self.follow_to_node_with_result(target_result=self.FollowResult.ARRIVED_AT_NODE)

    def follow_to_node_with_result(self, target_result: FollowResult):
        """
        Tries to follow the line to a node and returns the given target_result if a node is reached successfully.
        Returns FollowResult.TIMED_OUT otherwise.
        """

        self.p_controller.reset()
        obstacle_check_due = True # Only check for obstacles every second iteration -> higher infrared check frequency

        # Initial 'take-off' boost
        self.motor.setMotors(self.base_speed*3, self.base_speed*3)
        while self.infrared.update() == SensorBitmap.ALL:
            pass # Move off of current node

        # The line following loop.
        # The bitmap is checked for arrival twice, once after each other routine to
        # avoid missing an arrival.
        while True:
            if self.update_with_arrival_handler() == SensorBitmap.ALL:
                return target_result

            if obstacle_check_due and self.obstacle_ahead(threshold_cm=11):
                return self.handle_obstacle_encounter()
            obstacle_check_due = not obstacle_check_due

            bitmap = self.update_with_arrival_handler()
            if self.update_with_arrival_handler() == SensorBitmap.ALL:
                return target_result

            self.update_motors(bitmap)

    def update_with_arrival_handler(self) -> SensorBitmap:
        """
        Updates the InfraredSensor, returns the SensorBitmap and executes the node arrival
        routine if necessary before returning.
        This is intended to allow checking for arrival more often, as that is the most prone to being
        missed while something else (e.g., obstacle checker) is running.
        """

        bitmap = self.infrared.update()
        self.update_state(bitmap)

        if self.state == self.State.NODE_ARRIVAL:
            self.movement_routines.node_arrival()
            self.switch_state(self.State.IDLE)

        return bitmap


    def obstacle_ahead(self, threshold_cm: int) -> bool:
        """
        Returns whether the ultrasonic currently detects an obstacle ahead.
        Logs the distance to the obstacle if one is detected.
        Uses the given threshold to decide whether something is an obstacle.
        """

        if self.ultrasonic.get_distance_cm() < threshold_cm:
            # Double check to avoid one time errors
            time.sleep(0.01)
            distance = self.ultrasonic.get_distance_cm()
            if distance < threshold_cm:
                self.logger.log(f"Encountered obstacle (distance: {distance})")
                return True
        return False

    def update_motors(self, bitmap: SensorBitmap):
        """
        Updates the motors based on the given SensorBitmap.
        """

        correction = self.p_controller.compute_correction(bitmap)

        left_speed = self.base_speed - correction + self.drift_left_correction
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
        self.switch_state(self.State.PI_FOLLOW)
        return self.follow_to_node_with_result(target_result=self.FollowResult.PATH_BLOCKED)
