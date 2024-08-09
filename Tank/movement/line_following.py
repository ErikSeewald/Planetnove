from enum import Enum
from movement.movement_routines import MovementRoutines
from sensors.infrared import InfraredSensor, SensorBitmap
from movement.calibrated_motor import CalibratedMotor
import time


class LineFollower:
    """
    Class handling the robots main line following. Relies on the motor and sensor classes.
    Responsible for line following, node and obstacle detection and rotation adjustments.
    Does not make pathing decisions.
    """

    # FOLLOW RESULT
    class FollowResult(Enum):
        """
        Enum representing the result of a line following step
        """
        ARRIVED_AT_NODE = 1
        TIMED_OUT = -1

    # STRATEGY
    class StrategyState(Enum):
        IDLE = 0
        GO_FORWARD = 1
        GO_BACKWARD = -1
        ROTATE_LEFT = 2
        ROTATE_RIGHT = -2
        NODE_ARRIVAL = 3
    strategy: StrategyState

    bitmap_to_strategy: dict[SensorBitmap, StrategyState] = {
        SensorBitmap.LEFT: StrategyState.ROTATE_LEFT,
        SensorBitmap.RIGHT: StrategyState.ROTATE_RIGHT,
        SensorBitmap.MIDDLE: StrategyState.GO_FORWARD,
        SensorBitmap.ALL: StrategyState.NODE_ARRIVAL,
    }

    # SENSORS
    infrared: InfraredSensor
    motor: CalibratedMotor

    # CONTROL CLASSES
    movement_routines: MovementRoutines

    # ATTRIBUTES
    SECONDS_UNTIL_TIMEOUT: float = 60 # Maximum time for a line following step

    def __init__(self, sensor: InfraredSensor, motor: CalibratedMotor, movement_routines: MovementRoutines):
        self.infrared = sensor
        self.motor = motor
        self.movement_routines = movement_routines
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
            # In that case, continue to use StrategyState.LEFT.
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
        :return: FollowResult
        """

        # Only set strategy to forward if the current one is IDLE.
        # Otherwise it would also overwrite strategies set by other functions
        if self.strategy == self.StrategyState.IDLE:
            self.switch_strategy(self.StrategyState.GO_FORWARD)

        start_time = time.time()
        while time.time() - start_time < self.SECONDS_UNTIL_TIMEOUT:
            time.sleep(0.1)

            bitmap = self.infrared.update()
            self.update_strategy(bitmap)

            # STRATEGIES
            if self.strategy == self.StrategyState.ROTATE_LEFT:
                self.motor.rotate_left(seconds=0.05)

            elif self.strategy == self.StrategyState.ROTATE_RIGHT:
                self.motor.rotate_right(seconds=0.05)

            elif self.strategy == self.StrategyState.GO_FORWARD:
                self.motor.move_straight(seconds=0.1)

            elif self.strategy == self.StrategyState.NODE_ARRIVAL:
                self.movement_routines.node_arrival()
                self.switch_strategy(self.StrategyState.IDLE)
                return self.FollowResult.ARRIVED_AT_NODE

        return self.FollowResult.TIMED_OUT
