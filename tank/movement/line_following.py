from enum import Enum

from tank.movement.PID_controller import PIDController
from tank.movement.movement_routines import MovementRoutines
from tank.sensors.infrared import InfraredSensor, SensorBitmap
from tank.movement.calibrated_motor import CalibratedMotor
import time

from tank.sensors.ultrasonic import Ultrasonic
from util.logger import Logger


class LineFollower:
    """
    Class handling the robots main line following. Relies on the motor and sensor classes.
    Responsible for line following, node and obstacle detection and rotation adjustments.
    Does not make pathing decisions.
    """

    logger: Logger
    pid = PIDController
    base_speed = 0.8

    # FOLLOW RESULT
    class FollowResult(Enum):
        """
        Enum representing the result of a line following step
        """
        ARRIVED_AT_NODE = 1
        PATH_BLOCKED = 2
        TIMED_OUT = -1

    # STRATEGY
    class StrategyState(Enum):
        IDLE = 0
        PID_FOLLOW = 1
        NODE_ARRIVAL = 3

    strategy: StrategyState

    bitmap_to_strategy: dict[SensorBitmap, StrategyState] = {
        SensorBitmap.ALL: StrategyState.NODE_ARRIVAL,
    }

    # COMPONENT CLASSES
    infrared: InfraredSensor
    ultrasonic: Ultrasonic
    motor: CalibratedMotor

    # CONTROL CLASSES
    movement_routines: MovementRoutines

    # ATTRIBUTES
    SECONDS_UNTIL_TIMEOUT: float = 600 # Maximum time for a line following step

    def __init__(self, sensor: InfraredSensor, ultrasonic: Ultrasonic,
                 motor: CalibratedMotor, movement_routines: MovementRoutines, logger: Logger):
        self.logger = logger
        self.infrared = sensor
        self.ultrasonic = ultrasonic
        self.motor = motor
        self.movement_routines = movement_routines
        self.pid = PIDController(kp=1.0, ki=0.0, kd=0.1)
        self.switch_strategy(self.StrategyState.IDLE)

    def update_strategy(self, bitmap: SensorBitmap):
        """
        Updates the line following strategy based on the current state and the given SensorBitmap.
        """

        new_strat = self.bitmap_to_strategy.get(bitmap)

        if new_strat is not None:
            self.switch_strategy(new_strat)
        else:
            # For example, starting with SensorBitmap.LEFT and turning left to get to SensorBitmap.MIDDLE can result
            # in temporary SensorBitmap.NONE state where the black tape is inbetween the left and middle sensor.
            # In that case, continue to use StrategyState.PID_FORWARD.
            pass

    def switch_strategy(self, new_strategy: StrategyState):
        """
        Switches the line following strategy.
        Never change the strategy outside of this function.
        """

        self.strategy = new_strategy

    def follow_to_next_node(self) -> FollowResult:
        """
        Main line following loop that runs until the next node is reached or the loop times out.
        """

        # Only set strategy to forward if the current one is IDLE.
        # Otherwise, it would also overwrite strategies set by other functions
        if self.strategy == self.StrategyState.IDLE:
            self.switch_strategy(self.StrategyState.PID_FOLLOW)

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
            self.update_strategy(bitmap)

            # STRATEGIES
            if self.strategy == self.StrategyState.NODE_ARRIVAL:
                self.movement_routines.node_arrival()
                self.switch_strategy(self.StrategyState.IDLE)
                return target_result

            if self.strategy == self.StrategyState.PID_FOLLOW:
                # PID CONTROLLER
                correction = self.pid.compute_correction(bitmap)

                # MOTOR SPEEDS
                left_speed = self.base_speed - correction
                right_speed = self.base_speed + correction

                self.motor.PWM.setMotors(self.motor.c_left * left_speed,
                                         self.motor.c_right * right_speed)

        self.motor.PWM.stop()
        return self.FollowResult.TIMED_OUT

    def handle_obstacle_encounter(self) -> FollowResult:
        """
        Handles the case of the line follower encountering an obstacle and needing to turn back around to return
        to the starting node.
        """

        self.movement_routines.turn_around_avoid_obstacle()
        self.switch_strategy(self.StrategyState.PID_FOLLOW)
        return self.follow_to_node_with_result(target_result=self.FollowResult.PATH_BLOCKED)
